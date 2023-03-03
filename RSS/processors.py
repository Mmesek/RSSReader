from RSS.models import Feed_Post
from RSS.utils import processor


@processor
def blacklist(post: Feed_Post, value: str) -> bool:
    if value in post.content:
        post.feed.posts.remove(post)
        return True
