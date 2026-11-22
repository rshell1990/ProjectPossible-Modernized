
# This contains wrappers for the various Transform classes. It uses some
# of the classes in 00matrixcolor.rpy.

init -1400 python:


    class TransformMatrix(_BaseMatrix):
        """
        :undocumented:
        """

        function = None
        nargs = 0


        def __init__(self, *args):
            if len(args) != self.nargs:
                raise Exception("{} takes {} arguments, {} given.".format(type(self).__name__, self.nargs, len(args)))

            self.args = args


        def __call__(self, other, done):

            if type(other) is not type(self):
                return self.function(*self.args)
            else:
                args = tuple(a + (b - a) * done for a, b in zip(other.args, self.args))
                return self.function(*args)

        @staticmethod
        def _document(function):
            if not function:
                return ":undocumented:"

            rv = function.__doc__

            rv = rv.replace(":doc: matrix", ":doc: transform_matrix")
            rv = rv.replace("Returns", "A TransformMatrix that returns")

            return rv


    class OffsetMatrix(TransformMatrix):
        nargs = 3
        function = Matrix.offset
        __doc__ = TransformMatrix._document(Matrix.offset)

    class RotateMatrix(TransformMatrix):
        nargs = 3
        function = Matrix.rotate
        __doc__ = TransformMatrix._document(Matrix.rotate)

    class ScaleMatrix(TransformMatrix):
        nargs = 3
        function = Matrix.scale
        __doc__ = TransformMatrix._document(Matrix.scale)

