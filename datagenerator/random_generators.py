from util_functions import *
from datagenerator.operations import *


def seed_provider(master_seed):
    """
    :param master_seed: master seed
    :return: a generator of seeds, deterministically depending on the master one
    """
    state = RandomState(master_seed)
    max_int_32 = 2**31 - 1
    while True:
        yield state.randint(1, max_int_32)


class Parameterizable(object):
    """
    Mixin providing the ability to contain and update parameters.
    """

    def __init__(self, parameters):
        self.parameters = parameters

    def update_parameters(self, **kwargs):
        # TODO: ultimately, this can evolve into an Action operation => the
        # random generations characteristics evole over time

        # TODO2: cf discussion from Gautier: those parameters could become
        # columns of parameters => 1 value per actor
        self.parameters.update(kwargs)

        # TODO: this is actually not working: we need the sub-classes to
        # to "reload" accordingly...


class Generator(Parameterizable):
    """
    Independent parameterized random value generator.
    Abstract class
    """
    __metaclass__ = ABCMeta

    def __init__(self, parameters):
        Parameterizable.__init__(self, parameters)
        self.ops = self.GeneratorOps(self)

    @abstractmethod
    def generate(self, size):
        """
        "Independent" random value generation: do not depend on any previous
        observation, we just want to sample the random variable `size` times

        :param size: the number of random value to produce
        :return: an array of generated random values
        """
        pass

    class GeneratorOps(object):
        def __init__(self, generator):
            self.generator = generator

        class RandomValues(AddColumns):
            """
            Operation that produces one single column generated randomly.
            """

            def __init__(self, generator, named_as):
                AddColumns.__init__(self)
                self.generator = generator
                self.named_as = named_as

            def build_output(self, action_data):
                values = self.generator.generate(size=action_data.shape[0])
                return pd.DataFrame({self.named_as: values}, index=action_data.index)

        def generate(self, named_as):
            return self.RandomValues(self.generator, named_as=named_as)


class ConstantGenerator(Generator):
    def __init__(self, value):
        Generator.__init__(self, {})
        self.value = value

    def generate(self, size):
        return [self.value] * size


class NumpyRandomGenerator(Generator):
    """
        Generator wrapping any numpy.Random method.
    """

    def __init__(self, method, seed=None, **numpy_parameters):
        """Initialise a random number generator

        :param method: string: must be a valid numpy.Randomstate method that
            accept the "size" parameter

        :param numpy_parameters: dict, see descriptions below
        :param seed: int, seed of the generator
        :return: create a random number generator of type "gen_type", with its parameters and seeded.
        """
        Generator.__init__(self, numpy_parameters)
        self.numpy_method = getattr(RandomState(seed), method)

    def generate(self, size):
        all_params = merge_2_dicts({"size": size}, self.parameters)
        return self.numpy_method(**all_params)


class ScaledParetoGenerator(Generator):
    def __init__(self, m, seed=None, **numpy_parameters):
        Generator.__init__(self, numpy_parameters)

        self.stock_pareto = NumpyRandomGenerator(method="pareto", seed=seed,
                                                 **numpy_parameters)
        self.m = m

    def generate(self, size):
        stock_obs = self.stock_pareto.generate(size)
        return (stock_obs + 1) * self.m


class MSISDNGenerator(Generator):
    """

    """

    def __init__(self, countrycode, prefix_list, length, seed=None):
        """

        :param name: string
        :param countrycode: string
        :param prefix_list: list of strings
        :param length: int
        :param seed: int
        :return:
        """
        Generator.__init__(self, {})
        self.__cc = countrycode
        self.__pref = prefix_list
        self.__length = length
        self.seed = seed

        maxnumber = 10 ** length - 1
        self.__available = np.empty([maxnumber * len(prefix_list), 2],
                                    dtype=int)
        for i in range(len(prefix_list)):
            self.__available[i * maxnumber:(i + 1) * maxnumber, 0] = np.arange(0, maxnumber, dtype=int)
            self.__available[i * maxnumber:(i + 1) * maxnumber, 1] = i

    def generate(self, size):
        """returns a list of size randomly generated msisdns.
        Those msisdns cannot be generated again from this generator

        :param size: int
        :return: numpy array
        """

        available_idx = np.arange(0, self.__available.shape[0], dtype=int)
        generator = NumpyRandomGenerator(
            method="choice", a=available_idx, replace=False, seed=self.seed)

        generated_entries = generator.generate(size)
        msisdns = np.array(
            [self.__cc + self.__pref[self.__available[i, 1]] +
                str(self.__available[i, 0]).zfill(self.__length)
             for i in generated_entries])

        self.__available = np.delete(self.__available, generated_entries,
                                     axis=0)

        return msisdns


class DependentGenerator(Parameterizable):
    """
    Generator providing random values depending on some live observation
    among the fields of the action or attributes of the actors.

    This opens the door to "probability given" distributions
    """

    # TODO: observations is limited to one single column ("weights")

    __metaclass__ = ABCMeta

    def __init__(self, parameters):
        Parameterizable.__init__(self, parameters)
        self.ops = self.DependentGeneratorOps(self)

    @abstractmethod
    def generate(self, observations):
        """
        Generation of random values after observing the input events.

        :param observations: one list of "previous observations", coming from
        upstream operation in the Action or upstream random variables in this
        graph.

        :return: an array of generated random values
        """

        pass

    class DependentGeneratorOps(object):
        def __init__(self, generator):
            self.generator = generator

        class RandomValues(AddColumns):
            """
            Operation that produces one single column generated randomly.
            """

            def __init__(self, generator, named_as, observations_field,
                         attribute):
                AddColumns.__init__(self)

                if not ((attribute is None) ^ (observations_field is None)):
                    raise ValueError("can only depend on exactly one of "
                                     "attribute or observation_field")

                self.generator = generator
                self.named_as = named_as
                self.observations_field = observations_field
                self.attribute = attribute

            def build_output(self, action_data):
                # observing either a field or an attribute
                if self.observations_field is not None:
                    obs = action_data[self.observations_field]
                else:
                    obs = self.attribute.get_values(action_data.index)

                values = self.generator.generate(observations=obs)
                return pd.DataFrame({self.named_as: values},
                                    index=action_data.index)

        def generate(self, named_as, observed_field=None,
                     observed_attribute=None):
            return self.RandomValues(self.generator, named_as,
                                     observed_field, observed_attribute)


class DependentTriggerGenerator(DependentGenerator):
    """
    A trigger is a boolean Generator.

    A dependent trigger transforms, with the specified function, the value
    of the depended on action field or actor attribute into the [0, 1] range
    and uses that as the probability of triggering (i.e. of returning True)

    """

    def __init__(self, value_mapper=identity, seed=None):

        # random baseline to compare to each the activation
        DependentGenerator.__init__(self, {})
        self.base_line = NumpyRandomGenerator(method="uniform",
                                              low=0.0, high=1.0,
                                              seed=seed)
        self.value_mapper = value_mapper

    def generate(self, observations):
        probs = self.base_line.generate(size=observations.shape[0])
        triggers = self.value_mapper(observations)

        return probs < triggers
