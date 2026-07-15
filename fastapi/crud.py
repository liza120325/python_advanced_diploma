from typing import Annotated
from pathlib import Path
from sqlalchemy import select, update, insert, delete, and_, func, or_
from sqlalchemy.orm import selectinload
from fastapi import Header
from database import async_session, User, Likes, Twits, Images


async def create_data() -> None | str:
    """
    Функция наполняет базу данных первичной информацией
    :return: None
    """
    async with async_session() as start_session:
        async with start_session.begin():
            try:
                user_1 = User(name="Harry Potter", api_key="test")
                user_2 = User(name="Hermione Granger", api_key="herm")
                user_3 = User(name="Ron Weasley", api_key="ron")
                user_4 = User(name="Albus Dumbledore", api_key="albus")
                user_5 = User(name="Lord Voldemort", api_key="lord")
                user_6 = User(name="Bellatrix Lestrange", api_key="bella")
                user_7 = User(name="Minerva McGonagall", api_key="minerva")

                start_session.add_all(
                    [user_1, user_2, user_3, user_4, user_5, user_6, user_7]
                )

                user_1.followers = [user_2, user_3]
                user_1.following = [user_2, user_3, user_4, user_5, user_6, user_7]
                user_2.following = [user_3, user_4, user_5]
                user_6.following = [user_1, user_5]
                user_4.followers = [user_1, user_2, user_3]

                tweet_1 = Twits(context="I am the chosen one", author=1)
                tweet_2 = Twits(context="It is leviOsa, not leviosA", author=2)
                tweet_3 = Twits(
                    context="My dad works at the ministry of magic", author=3
                )
                tweet_4 = Twits(
                    context="Harry, you must find the horcruxes alone", author=4
                )
                tweet_5 = Twits(context="Avadacedavra!", author=5)
                tweet_6 = Twits(context="I killed Sirius Black", author=6)
                tweet_7 = Twits(context="Protect Hogwarts!", author=7)

                start_session.add_all(
                    [tweet_1, tweet_2, tweet_3, tweet_4, tweet_5, tweet_6, tweet_7]
                )

                like_1 = Likes(user_id=1, user_name="Harry Potter", tweet_id=1)
                like_2 = Likes(user_id=2, user_name="Hermione Granger", tweet_id=1)
                like_3 = Likes(user_id=4, user_name="Albus Dumbledore", tweet_id=2)

                start_session.add_all([like_1, like_2, like_3])

            except Exception as ex:
                return (
                    f"'result': 'false', 'error_type': {type(ex).__name__}, "
                    f"'error_message': {str(ex)}"
                )


async def get_my_profile(api_key: Annotated[str, Header()], cur_session) -> User | str:
    """
    Функция по получению профиля текущего пользователя
    :param api_key: api_key текущего пользователя
    :return: User
    """
    try:
        user = await cur_session.execute(
            select(User)
            .where(User.api_key == api_key)
            .options(selectinload(User.following), selectinload(User.followers))
        )
        result = user.scalars().first()
        return result

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def get_any_user_profile(user_id, cur_session) -> User | str:
    """
    Функция по получению информации о профиле любого пользователя
    :param user_id: ID пользователя, информацию о профиле которого хотим получить
    :return: User
    """
    try:
        user = await cur_session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.following), selectinload(User.followers))
        )
        result = user.scalars().first()
        return result

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def form_data_for_user(result) -> dict:
    """
    Функция формирует словарь для отправки данных страницы пользователя
    :param result: объект класса User
    :return: data = {User}
    """
    data = {
        "result": "true",
        "user": {
            "id": result.id,
            "name": result.name,
            "followers": [{"id": x.id, "name": x.name} for x in result.followers],
            "following": [{"id": x.id, "name": x.name} for x in result.following],
        },
    }
    return data


async def form_path_for_media(file) -> Path:
    """
    Функция формирует путь для сохранения изображения, полученного с твитом
    :param file: Изображение, отправленное с твитом
    :return: Путь для сохранения изображения
    """
    directory = Path("../static/media")
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / f"{file.filename}"
    return file_path


async def update_tweet_id_in_images(
    tweet_images, new_tweet_id, cur_session
) -> None | str:
    """
    Функция обновляет в таблице изображений ID твита.
    :param tweet_images: Изображение к твиту.
    :param new_tweet_id: ID твита с картинкой
    :return: None
    """
    try:
        await cur_session.execute(
            update(Images)
            .where(Images.media_id == tweet_images[0])
            .values(tweet_id=new_tweet_id)
        )
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def add_new_tweet(tweet_context, user_me, cur_session) -> None | str:
    """
    Функция добавляет новый твит в БД
    :param tweet_context: Текст твита
    :param user_me: Текущий пользователь
    :return: None | str
    """
    try:
        stmt = (
            insert(Twits)
            .values(context=tweet_context, author=user_me.id)
            .returning(Twits.id)
        )
        result = await cur_session.execute(stmt)
        new_tweet_id = result.scalar()
        await cur_session.commit()
        return new_tweet_id

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def deleting_tweet(user_me, id, cur_session) -> None | str:
    """
    Функция удаляет твит из БД
    :param user_me: Текущий пользователь
    :param id: ID твита, который удаляется
    :return: None | str
    """
    try:
        await cur_session.execute(
            delete(Twits).where(and_(Twits.author == user_me.id, Twits.id == id))
        )
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def add_following(user_me, user_following, cur_session) -> None | str:
    """
    Функция по оформлению подписки на пользователя
    :param user_me: Текущий пользователь
    :param user_following: Пользователь, на которого подписываемся
    :return: None | str
    """
    try:
        # Оформляем подписку
        user_me.following.append(user_following)
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def delete_following(user_me, user_following, cur_session) -> None | str:
    """
    Функция на удаление подписки
    :param user_me: Текущий пользователь
    :param user_following: Пользователь, от которого отписываемся
    :return: None | str
    """
    try:
        user_me.following.remove(user_following)
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def send_like_for_tweet(user_me, id, cur_session) -> None | str:
    """
    Функция ставит лайк на твит
    :param user_me: Текущий пользователь
    :param id: ID твита, на который савится лайк
    :return: None | str
    """
    try:
        await cur_session.execute(
            insert(Likes).values(
                user_id=user_me.id, user_name=user_me.name, tweet_id=id
            )
        )
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def delete_like_from_tweet(user_me, id, cur_session) -> None | str:
    """
    Функция удаляет лайк с твита
    :param user_me: Текущий пользователь
    :param id: ID твита, с которого удаляется лайк
    :return: None | str
    """
    try:
        await cur_session.execute(
            delete(Likes).where(and_(Likes.tweet_id == id, Likes.user_id == user_me.id))
        )
        await cur_session.commit()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )


async def get_list_of_tweets(user_me, following, cur_session) -> Twits | str:
    """
    Функция по получению твитов текущего пользователя, а также тех, на кого он подписан
    :param user_me: Текущий пользователь
    :param following: Список подписок текущего пользователя
    :return: Twits
    """
    try:
        likes_subquery = (
            select(func.count(Likes.id))
            .where(Likes.tweet_id == Twits.id)
            .correlate(Twits)
            .scalar_subquery()
        )
        # Получаем твиты
        query = await cur_session.execute(
            select(Twits, likes_subquery.label("likes_count"))
            .options(
                selectinload(Twits.likes),
                selectinload(Twits.attachments),
                selectinload(Twits.user_id),
            )
            .where(or_(Twits.author.in_(following), Twits.author == user_me.id))
            .order_by(likes_subquery.desc())
        )
        tweets = query.scalars().all()

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )

    return tweets


async def collect_data_for_tweets(tweets) -> list[Twits] | str:
    """
    Функция по преобразованию данных твитов в требуемый формат в ТЗ
    :param tweets:
    :return: list[Twits]
    """
    try:
        tweets_list = []
        for tweet in tweets:
            twit = {
                "id": tweet.id,
                "content": tweet.context,
                "attachments": [
                    f"/api/medias/{media.media_id}" for media in tweet.attachments
                ],
                "author": {"id": tweet.user_id.id, "name": tweet.user_id.name},
                "likes": [
                    {"user_id": x.user_id, "name": x.user_name} for x in tweet.likes
                ],
            }
            tweets_list.append(twit)

    except Exception as ex:
        return (
            f"'result': 'false', 'error_type': {type(ex).__name__}, "
            f"'error_message': {str(ex)}"
        )

    return tweets_list
