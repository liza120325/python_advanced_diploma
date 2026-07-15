from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

# 1. Строка подключения
DATABASE_URL = "postgresql+asyncpg://admin:secretpassword@db:5432/fastapi_db"

# 2. Создание асинхронного движка
# echo=True будет логгировать в консоль все sql запросы, которые мы будем делать
engine = create_async_engine(DATABASE_URL, echo=True)
# expire_on_commit=False will prevent attributes from being expired
# after commit.

# 3. Фабрика асинхронных сессий
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)
session = async_session()
Base = declarative_base()


async def get_db():
    async with async_session() as as_session:
        yield as_session


class User(Base):
    """Модель пользователя"""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    api_key = Column(String, default=0)

    # На кого ПОДПИСАН этот пользователь (тех, кого он читает)
    following = relationship(
        "User",
        lambda: user_following,
        primaryjoin=lambda: User.id == user_following.c.i_follow,
        secondaryjoin=lambda: User.id == user_following.c.i_am_followed,
        back_populates="followers",
    )

    # ПОДПИСЧИКИ этого пользователя (те, кто читают его)
    followers = relationship(
        "User",
        lambda: user_following,
        primaryjoin=lambda: User.id == user_following.c.i_am_followed,
        secondaryjoin=lambda: User.id == user_following.c.i_follow,
        back_populates="following",
    )

    twits = relationship(
        "Twits", back_populates="user_id", cascade="all, delete-orphan"
    )

    like_from_user_id = relationship(
        "Likes", back_populates="user_id_relationship", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f'"id": {self.id}, "name": {self.name}'


user_following = Table(
    "user_following",
    Base.metadata,
    Column("i_follow", Integer, ForeignKey(User.id), primary_key=True),
    Column("i_am_followed", Integer, ForeignKey(User.id), primary_key=True),
)


class Twits(Base):
    """Модель твитов, написанных пользователем"""

    __tablename__ = "twits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    context = Column(String, nullable=False)
    author = Column(Integer, ForeignKey("user.id"))

    # Связь с таблицей лайков
    likes = relationship("Likes", cascade="all, delete-orphan")
    # Связь с таблицей изображений
    attachments = relationship(
        "Images", back_populates="tweet", cascade="all, delete-orphan"
    )

    user_id = relationship("User", back_populates="twits")

    def __repr__(self) -> str:
        return (
            f'"id": {self.id}, "context": {self.context}, "attachments": {self.attachments}, '
            f'"author": {self.author}, "likes": {self.likes}'
        )


class Likes(Base):
    """Модель лайков, поставленных на твит"""

    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ID пользователя, поставившего лайк
    user_id = Column(Integer, ForeignKey("user.id"))
    user_name = Column(String)

    # Связь с таблицей Пользователь
    user_id_relationship = relationship("User", back_populates="like_from_user_id")

    # ID твита, на который поставили лайк
    tweet_id = Column(Integer, ForeignKey("twits.id", ondelete="CASCADE"))

    def __repr__(self) -> str:
        return f'"user_id": {self.user_id}, "name": {self.user_name}'


class Images(Base):
    """Модель картинок к твиту"""

    __tablename__ = "images"

    media_id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(Integer, ForeignKey("twits.id", ondelete="CASCADE"), default=None)
    path = Column(String)

    # Связь с таблицей твитов
    tweet = relationship("Twits", back_populates="attachments")

    def __repr__(self) -> str:
        return f"{self.path}"
