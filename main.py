from telebot import types
from telebot.async_telebot import AsyncTeleBot
import asyncio
import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time



def get_message_text(message: types.Message) -> str:
    text = message.json['text']
    return text[text.find(' ') + 1:]


TOKEN = "5818816840:AAF4t_MYRAXgVru_Z-idg6UqtzkTZAJzDUo"

bot = AsyncTeleBot(TOKEN)

engine = create_engine("sqlite:///data.db", connect_args={'check_same_thread': False}, echo=True)
models.Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

def CreateGame(): 
    global LocationMap
    LocationMap = dict()
    global NearbyLocationMap
    NearbyLocationMap = dict()
    Locations = [models.Location(0, 0, 0, "town"), models.Location(1, 10, 0, "town"),
        models.Location(2, 0, 10, "dungeon"), models.Location(3, -10, 0, "town"), models.Location(4, 0, -10, "dungeon"), 
        models.Location(-1, 40, 40, "town")]
    for loc1 in Locations:
        LocationMap[loc1.LocationID] = dict()
        NearbyLocationMap[loc1.LocationID] = set()
        for loc2 in Locations:
            if loc2.LocationID != loc1.LocationID:
                dist = abs(loc1.XCoord - loc2.XCoord + loc1.YCoord - loc2.YCoord)
                LocationMap[loc1.LocationID][loc2.LocationID] = (loc2.LocationType, dist) # храним только нужное для экономии памяти
                if dist <= 10:
                    NearbyLocationMap[loc1.LocationID].add(loc2.LocationID)
            
    Items = [models.Item(0, "basic sword", 10, "melee", 0, 0, 20, 0, 0, 0, 0, 0, -1),
            models.Item(1, "health potion", 10, "potion", 10, 0, 0, 0, 0, 0, 0, 3, -1),
            models.Item(2, "magic sword", 25, "melee", 0, 0, 20, 10, 0, 0, 0, 1, -1),
            models.Item(3, "Armour with magic resistance", 20, "armour", 0, 0, 0, 0, 20, 10, 0, 0, -1)]
    for location in Locations:
        session.add(location)
    for item in Items:
        session.add(item)
    session.commit()

@bot.message_handler(commands=['start'])
async def hello_message(message):
    await bot.send_message(message.chat.id,"Путник, заходи в самую известную кузню континента. Как твое имя?(/introduce <имя>)")

@bot.message_handler(commands=['introduce'])
async def introduce(message):
    if session.query(models.Player).get(message.chat.id) is None:
        session.add(models.Player(message.chat.id, get_message_text(message)))
        session.commit()
        await bot.send_message(message.chat.id, "Ага, так ты не местный. Покупать что-то будешь?")
    else:
        await bot.send_message(message.chat.id, "Эй, так я вспомнил тебя - раньше ты был под другим именем. Может стоит покинуть город?(/delete начать заново)")


@bot.message_handler(commands=['delete'])
async def delete(message):
    session.query(models.Player).filter(models.Player.UserID==message.chat.id).delete()
    session.commit()
    await bot.send_message(message.chat.id, "Прощай, путник")

@bot.message_handler(commands='see_for_sale')
async def see_for_sale(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    cur_loc = session.query(models.Location).get(cur_player.LocationID)
    if cur_loc.LocationType == "town":
        for item in cur_loc.Items:
            await bot.send_message(message.chat.id, item.info())
    else:
        await bot.send_message(message.chat.id, "Action not allowed here")

@bot.message_handler(commands=["stats"])
async def stats(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    await bot.send_message(message.chat.id, cur_player.stats())

@bot.message_handler(commands=["inventory"])
async def inventory(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    await bot.send_message(message.chat.id, "Your Inventory:")
    for item_stats in cur_player.inventory():
        await bot.send_message(message.chat.id, item_stats)

@bot.message_handler(commands=["use", "equip"])
async def use(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    item_to_use = session.query(models.Item).filter(models.Item.PlayersID==cur_player.UserID, models.Item.ItemName==get_message_text(message)).first()
    if item_to_use is None:
        await bot.send_message(message.chat.id, "You do not have this item")
        return
    if item_to_use.ItemType != "potion":
        item_to_deactivate = session.query(models.Item).filter(models.Item.ItemType==item_to_use.ItemType, models.Item.Active).first()
        item_to_use.Active = True
        if item_to_deactivate is not None:
            cur_player.Attack -= item_to_deactivate.Attack
            cur_player.MagicAttack -= item_to_deactivate.MagicAttack
            cur_player.Armour -= item_to_deactivate.Armour
            cur_player.MagicArmour -= item_to_deactivate.MagicArmour
        cur_player.Attack += item_to_use.Attack
        cur_player.MagicAttack += item_to_use.MagicAttack
        cur_player.Armour += item_to_use.Armour
        cur_player.MagicArmour += item_to_use.MagicArmour
        # Несмотря на описание гораздо логичнее если нельзя одновременно носить много оружий одного типа, поэтому позволил себя немного вольности в гейм-дизайне
        session.commit()
        await bot.send_message(message.chat.id, f"Now you use: {item_to_use.ItemName} as {item_to_use.ItemType} item")
    else:
        cur_player.CurHP += item_to_use.HP
        cur_player.CurMagicka += item_to_use.Magicka
        session.query(models.Item).filter(models.Item.ItemID==item_to_use.ItemID).delete()
        session.commit()
        bot.send_message(message.chat.id, f"You drank {item_to_use.ItemName}")

@bot.message_handler(commands=["unequip"])
async def stop_using(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    item_to_deactivate = session.query(models.Item).filter(models.Item.PlayersID==cur_player.UserID, models.Item.ItemName==get_message_text(message)).first()
    if item_to_deactivate is None:
        await bot.send_message(message.chat.id, "You do not have this item")
        return
    item_to_deactivate.Active = False
    cur_player.Attack -= item_to_deactivate.Attack
    cur_player.MagicAttack -= item_to_deactivate.MagicAttack
    cur_player.Armour -= item_to_deactivate.Armour
    cur_player.MagicArmour -= item_to_deactivate.MagicArmour
    await bot.send_message(message.chat.id, f"You unequiped {item_to_deactivate.ItemName}")
    
    

@bot.message_handler(commands=["buy"])
async def buy_item(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    item_to_buy = session.query(models.Item).filter(models.Item.PlayersID==-1, models.Item.ItemName==get_message_text(message), models.Item.InLocationID==cur_player.LocationID).first()
    if item_to_buy is None:
        await bot.send_message(message.chat.id, "This is not sold here")
        return
    if (cur_player.Level >= item_to_buy.ReqLevel and cur_player.Money >= item_to_buy.Cost):
        item_to_buy.PlayersID = cur_player.UserID
        cur_player.Money -= item_to_buy.Cost
        await bot.send_message(message.chat.id, f"New Item: {item_to_buy.ItemName}")
    else:
        await bot.send_message(message.chat.id, "You cannot buy this item yet")

@bot.message_handler(commands=["sell"])
async def buy_item(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    item_to_sell = session.query(models.Item).filter(models.Item.PlayersID==cur_player.UserID, models.Item.ItemName==get_message_text(message)).first()
    if item_to_sell is None:
        await bot.send_message(message.chat.id, "You do not have this item")
        item_to_sell.PlayersID = -1
        cur_player.Money += item_to_sell.Cost
        await bot.send_message(message.chat.id, f"Sold Item: {item_to_sell.ItemName}")
        return

@bot.message_handler(commands=["map"])
async def map(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    await bot.send_message(message.chat.id, "Nearby locations:")
    to_send = ""
    for loc_id, loc_info in LocationMap[cur_player.LocationID].items():
        to_send += f"{loc_id} : {loc_info[0]}({loc_info[1]} miles away)\n"
    await bot.send_message(message.chat.id, to_send)

@bot.message_handler(commands=["travel"])
async def travel(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    new_loc = session.query(models.Location).get(int(get_message_text(message)))
    if new_loc is None or not new_loc.LocationID in NearbyLocationMap[cur_player.LocationID]:
        await bot.send_message(message.chat.id, "You cannot travel to this location")
        return
    time.sleep(LocationMap[cur_player.LocationID][new_loc.LocationID][1])
    cur_player.LocationID = new_loc.LocationID
    if new_loc.LocationType == "town":
        cur_player.CurHP = cur_player.HP
        cur_player.CurMagicka = cur_player.Magicka
        await bot.send_message(message.chat.id, "You arrived at a town.\nHelth and Magicka are restored")

@bot.message_handler(commands=['talk'])
async def button_message(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    if cur_player.ApprovedForTalk:
        cur_loc = session.query(models.Location).get(cur_player.LocationID)
        if cur_loc.LocationID == 0:
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1=types.KeyboardButton("Как идет торговля?")
            item2=types.KeyboardButton("Есть какая-то полезная информация?")
            markup.add(item1)
            markup.add(item2)
            await bot.send_message(message.chat.id, "А?", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "You cannot talk here")
    else:
        await bot.send_message(message.chat.id, "Говорю же - проваливай")

@bot.message_handler(commands=["fast_travel"])
async def fast_travel(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    if cur_player.ApprovedForFastTravel:
        if cur_player.LocationID == 0:
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1=types.KeyboardButton("За сколько подкинешь до столицы?")
            item2=types.KeyboardButton("Я от кузнеца")
            item4=types.KeyboardButton("Я от Йорика")
            markup.add(item1)
            markup.add(item2)
            markup.add(item4)
            await bot.send_message(message.chat.id, "Что нужно?", reply_markup=markup)
        else:
            await bot.send_message(message.chat.id, "You cannot fast travel here")
    else:
        await bot.send_message(message.chat.id, "Говорю же, правливай!")

@bot.message_handler(content_types='text')
async def message_reply(message):
    cur_player = session.query(models.Player).get(message.chat.id)
    if cur_player is None:
        await bot.send_message(message.chat.id, "Register First")
        return
    if cur_player.LocationID == 0:
        if message.text == "Как идет торговля?":
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1=types.KeyboardButton("Я первый раз в этом городе и хочу завести знакомства.")
            item2=types.KeyboardButton("Дерзишь? Пойду-ка я отсюда")
            markup.add(item1)
            markup.add(item2)
            await bot.send_message(message.chat.id, "Да неплохо, тебе то что?", reply_markup=markup)
        elif message.text == "Есть какая-то полезная информация?":
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1=types.KeyboardButton("Выкладывай(7 золотых)")
            markup.add(item1)
            await bot.send_message(message.chat.id,'Ха-ха, есть, но информация тут дорого стоит', reply_markup=markup)
        elif message.text == "Я первый раз в этом городе и хочу завести знакомства.":
            await bot.send_message(message.chat.id, f"Ну что же, {cur_player.Nickname}, тут не город а дыра. Отправляйся в столицу - она в 25 милях отсюда. Скажи извочику что ты от Йорика - он довезет тебя без проишествий")
        elif message.text == "Дерзишь? Пойду-ка я отсюда":
            await bot.send_message(message.chat.id, f"Ну и проваливай, больше болтать с тобой я не намерен")
        elif message.text == "Выкладывай(7 золотых)":
            if cur_player.Money >= 7:
                cur_player.Money -= 7
                await bot.send_message(message.chat.id, f"Ну что же, {cur_player.Nickname}, тут не город а дыра. Отправляйся в столицу - она в 25 милях отсюда. Скажи извочику что ты от Йорика - он довезет тебя без проишествий")
            else:
                await bot.send_message(message.chat.id, "Да у тебя денег столько нет")
        elif message.text == "За сколько подкинешь до столицы?":
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1=types.KeyboardButton("Поехали!")
            markup.add(item1)
            await bot.send_message(message.chat.id, "7 золотых до Ховедстада", reply_markup=markup)
        elif message.text == "Поехали!":
            cur_player.Money -= 7
            cur_player.LocationID = -1
            cur_player.CurHP = cur_player.HP
            cur_player.CurMagicka = cur_player.Magicka
            await bot.send_message(message.chat.id, "You arrived at the Capital.\nHelth and Magicka are restored")
        elif message.text == "Я от кузнеца":
            await bot.send_message(message.chat.id, "У меня таких клиентов по 10 за день. Ты же его небось не знаешь даже")
            cur_player.ApprovedForFastTravel = False
        elif message.text == "Я от Йорика":
            await bot.send_message(message.chat.id, "Друг Йорика - мой друг. Садись в повозку")
            cur_player.LocationID = -1
            cur_player.CurHP = cur_player.HP
            cur_player.CurMagicka = cur_player.Magicka
            await bot.send_message(message.chat.id, "You arrived at the Capital.\nHelth and Magicka are restored")


CreateGame()
asyncio.run(bot.polling())
