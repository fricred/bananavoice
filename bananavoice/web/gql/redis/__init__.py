"""Redis API."""

from bananavoice.web.gql.redis.mutation import Mutation
from bananavoice.web.gql.redis.query import Query

__all__ = ["Query", "Mutation"]
