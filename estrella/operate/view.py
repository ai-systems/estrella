import logging
from operator import attrgetter
from typing import TypeVar, List, Callable, Type, Iterable

from estrella.model.basic import Link
from estrella.interfaces import Loggable, Viewable


def safe_predicate(func):
    def f(*args, **kwargs):
        if not func:
            return True
        try:
            return func(*args, **kwargs)
        except:
            return False

    return f


U = TypeVar("U", bound=Viewable)


class View(List[U], Loggable):
    def __init__(self, initial_list: List[U]):
        super().__init__(initial_list)
        Loggable.__init__(self)
        self.initial_list = initial_list[:]
        self._view_type: Viewable = None

    @property
    def view_type(self):
        """
        Returns the type of the objects captured in this view.

        For now, only works with one single type.
        :return: Type of object captured in this view.
        """
        if not self._view_type:
            if len(self) > 0:
                self._view_type = type(self[0])  # TODO: Not very sophisticated, needs to be redone for multiple types
        return self._view_type

    def filter(self, filter_predicate: Callable = None, **kwargs):
        """
        Filters the view given a predicate.

        If no predicate is given, predicates will be constructed from keyword arguments (if present) to filter
        by exact match with the objects' attributes in this view.

        Example: ``view.filter(subject="He")`` will remove every ``obj`` from the view
        where ``getattr(obj, "subj", None) != "He"``

        :param filter_predicate: function of the signature `[obj] -> [Bool]` to filter by.
            Objects for which this function returns false are removed from the view.

        :param kwargs: If no filter_predicate is provided, predicates are constructed from keyword args.

        :return: Returns the filtered list.
        """
        if not filter_predicate and kwargs:
            filter_predicate = get_predicate(**kwargs)
        filtered = [x for x in filter(filter_predicate, self)]
        self.clear()
        self.extend(filtered)
        return self

    def for_each(self, func: Callable):
        """
        Executes a given function on every member of the view.

        Syntactic sugar m ``for m in view: func(m)``.
        :param func: function to execute.

        :return: The view.
        """
        for member in self:
            func(member)
        return self

    def expand(self, filter_predicate: Callable = None, source=None, **kwargs):
        """
        Expands the view with members from a given source that match a given predicate.

        If no source is provided, draws from the initial list given when creating the view.
        If no predicate is given, predicates will be constructed from keyword arguments (if present) to filter
        by exact match with the objects' attributes in this view.

        :param filter_predicate: function of the signature ``[obj] -> [Bool]`` to filter by.
            Objects for which this function returns ``false`` are not added to the view.

        :param source: Source to expand with. If none is given, draws from the initial list given when the view
            was created.

        :param kwargs: If no filter_predicate is provided, predicates are constructed from keyword args.

        :return: The view expanded with members from the given source passing the given predicate.
        """
        if not filter_predicate and kwargs:
            filter_predicate = get_predicate(**kwargs)
        source = source or self.initial_list
        self.extend(filter(safe_predicate(filter_predicate), source))
        return self

    def rank(self, comparator: Callable, reverse=False):
        """
        Syntactic sugar for ``view.sort(key=comparator, reverse=reverse)``.

        Refer to python documentation for ``sort`` on lists.
        """
        self.sort(key=comparator, reverse=reverse)
        return self

    def hop(self, link_name: str, constraint: Callable = None, keep=False):
        """
        Adds new members to the view which are reachable from the current members by a given attribute name.

        Example: ``v.hop(link_name="facts", constraint) will add all ``getattr(m, "facts", None) for m in v`` that
        satisfy constraint.

        If a member has no attribute with that name, nothing is added. If ``keep`` is False (default),
        the current members are discarded in favour of the new members.

        :param link_name: Name of the attribute of the current member. If the attribute is of type ``Link``,
            the target of the link is added.

        :param constraint: Constraint a new member has to fulfill in order to be added to the view.

        :param keep: Whether to keep the current members.

        :return: The view with new members which are reachable from the current members via a given attribute and
            satisfy a given condition.
        """
        # getattr link
        # if single: add it to candidates
        # if collection: for each, add
        # filter by constraint
        # create view from targets
        # return
        links = []
        for member in self:
            link = getattr(member, link_name, None)
            if link:
                try:
                    links.extend(link)  # assuming member.link_name is list
                except TypeError:
                    links.append(link)  # well then it's a single link
        result = [x.target if isinstance(x, Link) else x for x in filter(safe_predicate(constraint), links)]
        if not keep:
            self.clear()
        self.extend(result)
        self._view_type = None
        return self

    def copy(self):
        """
        Copys the view.

        Useful, since the operations on the view are stateful (yet to debate whether it makes sense).
        :return: Copy of the view.
        """
        return View(self[:])

    def serialize(self, serialize_with=None, **kwargs) -> str:
        """
        Serializes the view with a given serializer.

        :param serialize_with: what to serialize with. If None is given, just uses ``repr``

        :param kwargs: Keyword arguments that are supplied to the given serializer.

        :return: Serialized (to string) representation of the view.
        """
        if serialize_with:
            return serialize_with(self, **kwargs)
        else:
            return repr(self)

    def __repr__(self):
        return "View<{}>".format(self.view_type.__name__) + super().__repr__()


def create_from(from_what, view_type: Type[Viewable]) -> View:
    """
    Creates a view from a given instance.

    :param from_what: Instance to create the view from.

    :param view_type: Expected type of the view to be created.

    :return: The view of a given view type.
    """
    if isinstance(from_what, Iterable) and not isinstance(from_what, str):
        return View([x for fw in from_what for x in create_from(fw, view_type)])
    fm = view_type.get_factory_method(from_what)
    if fm:
        return View(fm(from_what))
    else:
        raise ValueError("Don't know how to create view {} from {}!".format(view_type.__name__, type(from_what)))


def get_predicate(**kwargs):
    @safe_predicate
    def pred(v):
        try:
            actuals = attrgetter(*kwargs.keys())(v)
        except AttributeError:
            logging.getLogger(__name__).warning("{} doesn't have one of the attributes {}".format(v, kwargs.keys()))
            return False
        if len(kwargs) < 2:
            actuals = [actuals]
        return all(actual == val for actual, val in zip(actuals, kwargs.values()))

    return pred
