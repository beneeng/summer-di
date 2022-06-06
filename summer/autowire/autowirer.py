

from collections import defaultdict
from typing import Any, Collection, DefaultDict, Dict, Optional, Set, Type

from summer.autowire.bean_initializer import BeanInitializer
from summer.autowire.bean_provider import BeanProvider
from summer import summer_logging
from summer.util import inspection_util
from summer.autowire.exceptions import CircularDependencyException, ValidationError


class Autowirer:

    def __init__(self, bean_providers: Collection[BeanProvider]) -> None:
        self.bean_providers = bean_providers # All providers
        # Candidates for a specific type, each initializer is candidate for the type and all its super types
        self.candidates : DefaultDict[Type, Set[BeanInitializer]] =  defaultdict(set) 
        self.initializers : Set[BeanInitializer] = set() # All Initializers
        self.beans: Optional[Dict[str, Any]] = None # resulting dict of beans, only loaded once

    def autowire_beans(self) -> Dict[str, Any]:
        if self.beans is None:
            self._load_candidate_map() # Load All candidates for all types into a map
            self._validate_dependencies() # check if all constraints are met 
            self.beans = self._autowire_beans() #do the autowiring
        return self.beans
        
    def _load_candidate_map(self):
        self.candidates = defaultdict(set)
        self.initializers = set()
        for provider in self.bean_providers:
            #create initializer for the bean
            initializer = BeanInitializer(provider)
            self.initializers.add(initializer)
            provides_type = provider.provides()
            # set this initializer as candidate for class and ancestors
            for provides in  inspection_util.get_all_base_classes(provides_type):
                self.candidates[provides].add(initializer)

    def _autowire_beans(self) -> Dict[str, Any]:
        collection_candidates = {} #candidates for collections
        initialized_initializers : Set[BeanInitializer] = set() # these are done
        uninitialized_initializers : Set[BeanInitializer] = self.initializers #these are still to do 
        changes = True
        while changes:
            uninitialized_initializers_tmp = set()
            changes = False
            for initializer in uninitialized_initializers:
                self._initialize_initializer(initializer, collection_candidates)

                if initializer.ready():
                    changes = True
                    initialized_initializers.add(initializer)
                    summer_logging.get_summer_logger().debug("Successfully initialized Bean \"%s\"", initializer.bean_name())
                else:
                    uninitialized_initializers_tmp.add(initializer)
            uninitialized_initializers = uninitialized_initializers_tmp
        
        if len(uninitialized_initializers) != 0:
            self._find_reason_for_failed_autowire(uninitialized_initializers)
        
        # now all collections have to be filled
        for candidate_type, candidate_collection in collection_candidates.items():
            _, itemtype = inspection_util.destruct_autowirable_collection(candidate_type)
            beans = [ i.get() for i in self.candidates[itemtype] ]
            if isinstance(candidate_collection, set):
                candidate_collection.update(beans)
            if isinstance(candidate_collection, list):
                candidate_collection.extend(beans)
        
        return { initializer.bean_name(): initializer.get() for initializer in initialized_initializers }

    def _initialize_initializer(self, initializer: BeanInitializer, collection_candidates: Dict[Type, Any]):
        for name, type_ in initializer.requires():
            collection, _ = inspection_util.destruct_autowirable_collection(type_)
            candidate = None
            # collections are just added as a list and filled later because of "pass by reference"
            if collection is not None: 
                if type_ not in collection_candidates:
                    collection_instance = collection()
                    collection_candidates[type_] = collection_instance
                candidate = collection_candidates[type_]

            else:
                # single candidate should be there because of the alidation (no ambiguous references)
                candidate_initializer = list(self.candidates[type_])[0]
                if candidate_initializer.ready():
                    candidate = candidate_initializer.get()

            if candidate is not None:
                initializer.add_parameter(name, candidate)

    def _find_reason_for_failed_autowire(self, uninitialized: Set[BeanInitializer]):
        summer_logging.get_summer_logger().warning("The following CircularDependencyException is just a guess and might be very unspecific")
        raise CircularDependencyException(", ".join([x.bean_name() for x in uninitialized]))


    def _validate_dependencies(self):
        summer_logging.get_summer_logger().debug("Validating beans")
        errors = []
        for provider in self.bean_providers:
            for pname, pannotation, phas_default in provider.requires():
                if inspection_util.is_autowirable_collection(pannotation):
                    # collections might be empty, so this is always possible
                    continue

                candidate_providers = self.candidates[pannotation]
                if len(candidate_providers) > 1:
                    errors.append(f'Too many candidates for dependency "{pname}" of bean "{provider.name()}"')
                    continue
                
                if len(candidate_providers) < 1 and not phas_default:
                    errors.append(f'No candidates for dependency "{pname}" of bean "{provider.name()}"')
                    continue

        if len(errors) != 0:
            error_string = "Can not autowire beans: \n" + "\n".join(errors)
            raise ValidationError(error_string)
        summer_logging.get_summer_logger().debug("Successfully validated dependencies for %s beans", len(self.bean_providers))