import graphene
from wagtailcommerce.accounts.object_types import UserObjectType


class UserQuery(graphene.ObjectType):
    user = graphene.Field(UserObjectType)

    def resolve_user(self, info, **kwargs):
        return info.context.user
