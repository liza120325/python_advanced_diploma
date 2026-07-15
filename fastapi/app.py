import logging
from contextlib import asynccontextmanager
from typing import Annotated

import aiofiles
from fastapi import FastAPI, Header, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from crud import (
    add_following,
    add_new_tweet,
    collect_data_for_tweets,
    create_data,
    delete_following,
    delete_like_from_tweet,
    deleting_tweet,
    form_data_for_user,
    form_path_for_media,
    get_any_user_profile,
    get_list_of_tweets,
    get_my_profile,
    send_like_for_tweet,
    update_tweet_id_in_images,
)
from database import Base, Images, async_session, engine
from schemas import (
    DoUndoLike,
    FollowUser,
    MediaOut,
    TweetDelete,
    TweetIn,
    TweetOut,
    TweetsByFollowing,
    UserOut,
)

logger = logging.getLogger("logger_for_app")
logging.basicConfig(level=logging.DEBUG, filename="fastapi.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await create_data()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/users/me", response_model=UserOut)
async def get_users_me(api_key: Annotated[str, Header()]) -> dict:
    """
    Эндпоинт по получению информации о профиле текущего пользователя.
    :param api_key: api_key текущего пользователя
    :return: объект класса User
    """
    async with async_session() as session:
        result = await get_my_profile(api_key, session)
        data = await form_data_for_user(result)

    return data


@app.get("/api/users/{user_id}", response_model=UserOut)
async def get_users_any(user_id: int) -> dict:
    """
    Эндпоинт по получению информации о профиле конкретного пользователя.
    :param user_id: ID пользователя, информацию о профиле которого хотим получить
    :return: объект класса User
    """
    async with async_session() as session:
        result = await get_any_user_profile(user_id, session)
        data = await form_data_for_user(result)

    return data


@app.post("/api/users/{id}/follow", response_model=FollowUser)
async def follow_user(api_key: Annotated[str, Header()], id: int) -> dict | str:
    """
    Эндпоинт на оформление подписки на пользователя
    :param api_key: api_key текущего пользователя
    :param id: ID пользователя, на которого подписываемся
    :return: data = {"result": "true"}
    """
    async with async_session() as session:

        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        user_following = await get_any_user_profile(id, session)
        logger.info(f"Получен пользователь на которого подписываемся {user_following}")

        logger.info("Проверяем подписку")
        check = user_following in user_me.following

        if not check:
            logger.info("Пользователь не подписан")
            await add_following(user_me, user_following, session)
            logger.info("Подписка оформлена")
        else:
            raise Exception(
                f"'result': 'false', 'error_type': {type(Exception).__name__}, "
                f"'error_message': {str(Exception)}"
            )

    data = {"result": "true"}
    return data


@app.delete("/api/users/{id}/follow", response_model=FollowUser)
async def unfollow_user(api_key: Annotated[str, Header()], id: int) -> dict | str:
    """
    Эндпоинт на отписку от пользователя
    :param api_key: api_key текущего пользователя
    :param id: ID пользователя, от которого отписываемся
    :return: data = {"result": "true"}
    """
    async with async_session() as session:

        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        user_following = await get_any_user_profile(id, session)
        logger.info(f"Получен пользователь, от которого отписываемся {user_following}")

        logger.info(
            "Проверяем, подписан ли текущий пользователь на того, от кого он хочет отписаться"
        )
        check = user_following in user_me.following

        if check:
            await delete_following(user_me, user_following, session)
            logger.info("Успешно отписались")
        else:
            raise Exception(
                f"'result': 'false', 'error_type': {type(Exception).__name__}, "
                f"'error_message': {str(Exception)}"
            )

    data = {"result": "true"}
    return data


@app.post("/api/tweets/{id}/likes", response_model=DoUndoLike)
async def send_like(api_key: Annotated[str, Header()], id: int) -> dict:
    """
    Эндпоинт ставит лайк на твит.
    :param api_key: api_key текущего пользователя.
    :param id: ID твита, на который ставится лайк.
    :return: data = {"result": "true"}
    """
    async with async_session() as session:

        # Получаем ID и Имя пользователя, который ставит лайк
        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        await send_like_for_tweet(user_me, id, session)
        logger.info("Добавлены ID и Имя пользователя, ID твита в таблицу лайков")

    data = {"result": "true"}
    return data


@app.delete("/api/tweets/{id}/likes", response_model=DoUndoLike)
async def unsend_like(api_key: Annotated[str, Header()], id: int) -> dict:
    """
    Эндпоинт по удалению лайка с твита.
    :param api_key: api_key текущего пользователя.
    :param id: ID твита, у которого удаляется лайк.
    :return: data = {"result": "true"}
    """
    async with async_session() as session:

        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        await delete_like_from_tweet(user_me, id, session)
        logger.info("Лайк удален")

    data = {"result": "true"}
    return data


@app.post("/api/medias", response_model=MediaOut)
async def post_new_media(api_key: Annotated[str, Header()], file: UploadFile) -> dict:
    """
    Эндпоинт сохраняет картинки в базу данных.
    :param api_key: api_key текущего пользователя.
    :param file: картинка к твиту.
    :return: присвоенный ID отправленной картинки.
    """
    # Сохранить файл
    file_path = await form_path_for_media(file)
    contents = file.file.read()

    async with aiofiles.open(str(file_path), mode="wb") as f:
        await f.write(contents)
        logger.info("Файл сохранен")

    async with async_session() as session:
        # Внести в базу данных путь к папке с изображением
        new_file = Images(path=str(file_path))
        logger.info("Файл добавлен в БД")
        session.add(new_file)
        await session.commit()

    data = {"result": "true", "media_id": new_file.media_id}
    return data


@app.post("/api/tweets", response_model=TweetOut)
async def post_new_tweet(api_key: Annotated[str, Header()], tweet: TweetIn) -> dict:
    """
    Эндпоинт на публикацию нового твита.
    :param api_key: api_key текущего пользователя.
    :param tweet: твит от пользователя.
    :return: присвоенный ID отправленному твиту.
    """
    tweet_context = tweet.tweet_data
    tweet_images = tweet.tweet_media_ids

    async with async_session() as session:

        # Получаем автора твита
        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        # Добавляем новый твит
        new_tweet_id = await add_new_tweet(tweet_context, user_me, session)
        logger.info("Твит добавлен в БД")

        # Добавляем изображение к новому твиту
        if tweet_images:
            logger.info("Твит содержит картинку")
            await update_tweet_id_in_images(tweet_images, new_tweet_id, session)
            return {"result": "true", "tweet_id": new_tweet_id}

        else:
            return {"result": "true", "tweet_id": new_tweet_id}


@app.delete("/api/tweets/{id}", response_model=TweetDelete)
async def delete_tweet(api_key: Annotated[str, Header()], id: int) -> dict | str:
    """
    Эндпоинт на удаление твита.
    :param api_key: api_key текущего пользователя.
    :param id: ID удаляемого твита
    :return: data = {"result": "true"}
    """
    async with async_session() as session:
        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        await deleting_tweet(user_me, id, session)
        logger.info("Твит удален")

    data = {"result": "true"}
    return data


@app.get("/api/medias/{media_id}")
async def get_pictures(media_id: int) -> FileResponse:
    """
    Эндпоинт на отдачу картинки твита
    :param media_id: ID картинки
    :return: FileResponse
    """
    async with async_session() as session:
        get_picture_path = await session.execute(
            select(Images.path).where(Images.media_id == media_id)
        )
        image_path = get_picture_path.scalars().first()

        return FileResponse(image_path)


@app.get("/api/tweets", response_model=TweetsByFollowing)
async def get_tweets(api_key: Annotated[str, Header()]) -> dict:
    async with async_session() as session:
        user_me = await get_my_profile(api_key, session)
        logger.info(f"Получен текущий пользователь {user_me}")

        following = [x.id for x in user_me.following]
        logger.info(f"Получены подписки текущего пользователя {following}")

        tweets = await get_list_of_tweets(user_me, following, session)
        logger.info(f"Получены твиты  {tweets}")

        tweets_list = await collect_data_for_tweets(tweets)
        logger.info("Преобразованы данные для отправки")

        data = {"result": "true", "tweets": tweets_list}
        return data
