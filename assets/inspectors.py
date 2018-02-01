"""
Extensions to `drf-yasg <https://drf-yasg.readthedocs.io/>`_.

"""
from drf_yasg.inspectors import SwaggerAutoSchema as BaseSwaggerAutoSchema


class SwaggerAutoSchema(BaseSwaggerAutoSchema):
    """
    An extension to the :py:class:`drf_yasg.inspectors.SwaggerAutoSchema` class which knows about a
    few more Operation properties.

    """

    extra_properties = ['security']
    """
    Additional properties which may be set on operations. Prefix the properties with ``operation_``
    and pass them as additional keyword arguments to :py:func:`swagger_auto_schema`.

    """

    def get_operation(self, *args, **kwargs):
        operation = super().get_operation(*args, **kwargs)
        for key in self.extra_properties:
            value = self.overrides.get('operation_' + key)
            if value is not None:
                operation[key] = value
        return operation
