from pydantic import BaseModel, Field


class Follow(BaseModel):
    id: int
    name: str


class User(BaseModel):
    id: int
    name: str
    followers: list[Follow] = Field(default_factory=list)
    following: list[Follow] = Field(default_factory=list)


class UserOut(BaseModel):

    result: bool
    user: User

    class Config:
        orm_mode = True


class TweetOut(BaseModel):

    result: bool
    tweet_id: int

    class Config:
        orm_mode = True


class TweetIn(BaseModel):

    tweet_data: str
    tweet_media_ids: list[int] | None


class MediaIn(BaseModel):

    tweet_id: int


class MediaOut(BaseModel):

    result: bool
    media_id: int

    class Config:
        orm_mode = True


class FollowUser(BaseModel):

    result: bool

    class Config:
        orm_mode = True


class TweetDelete(BaseModel):

    result: bool

    class Config:
        orm_mode = True


class Author(BaseModel):
    id: int
    name: str


class Likes(BaseModel):
    user_id: int
    name: str


class TweetInfo(BaseModel):
    id: int
    content: str
    attachments: list[str | None] = Field(default_factory=list)
    author: Author
    likes: list[Likes] = Field(default_factory=list)


class TweetsByFollowing(BaseModel):

    result: bool
    tweets: list[TweetInfo] = Field(default_factory=list)

    class Config:
        orm_mode = True


class DoUndoLike(BaseModel):

    result: bool

    class Config:
        orm_mode = True


class SendMediaId(BaseModel):

    media_id: str

    class Config:
        orm_mode = True


class TweetId(BaseModel):
    id: int
