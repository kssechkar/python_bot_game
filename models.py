from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    UserID = Column("UserID", Integer, primary_key=True)
    Nickname = Column("Nickname", String)
    Level = Column("Level", Integer)
    HP = Column("HP", Integer)
    CurHP = Column("CurHP", Integer)
    Money = Column("Money", Integer)
    Attack = Column("Attack", Integer)
    Magicka = Column("Magicka", Integer)
    CurMagicka = Column("CurMagicka", Integer)
    MagicAttack = Column("MagicAttack", Integer)
    MagicAttackCost = Column("MagicAttackCost", Integer)
    XP = Column("XP", Integer)
    Armour = Column("Armour", Integer)
    MagicArmour = Column("MagicArmour", Integer)
    LocationID = Column("LocationID", Integer)
    ApprovedForFastTravel = Column("ApprovedForFastTravel", Boolean)
    ApprovedForTalk = Column("ApprovedForTalk", Boolean)

    Items = relationship("Item", backref="player")

    def __init__(self, UserID, Nickname):
        self.UserID = UserID
        self.Nickname = Nickname
        self.Level = 0
        self.HP = 100
        self.CurHP = 100
        self.Money = 14
        self.Attack = 10
        self.Magicka = 100
        self.CurMagicka = 100
        self.MagicAttackCost = 50
        self.MagicAttack = 30
        self.XP = 0
        self.Armour = 0
        self.MagicArmour = 0
        self.LocationID = 0
        self.ApprovedForFastTravel = True
        self.ApprovedForTalk = True
    
    def stats(self):
        return f"Name: {self.Nickname}\nLevel: {self.Level}\nCurHP: {self.CurHP}\nMoney: {self.Money}\nAttack: {self.Attack}\nMagicka: {self.Magicka}\nMagicAttack: {self.MagicAttack}\nMagicAttackCost: {self.MagicAttackCost}\nXP: {self.XP}\nArmour: {self.Armour}\nMagicArmour: {self.MagicArmour}\n"
    
    def inventory(self):
        ret = []
        for item in self.Items:
            ret.append(item.info())
        return ret



class Mob(Base):
    __tablename__ = "mobs"

    MobID = Column("MobID", Integer, primary_key=True)
    MobName = Column("MobName", String)
    HP = Column("HP", Integer)
    XP = Column("XP", Integer)
    ReqLevel = Column("ReqLevel", Integer)
    AttackType = Column("AttackType", String)
    Attack = Column("Attack", Integer)
    Armour = Column("Armour", Integer)
    MagicArmour = Column("Armour", Integer)

    def __init__(self, MobID, MobName, HP, XP, ReqLevel, AttackType, Attack, Armour, MagicArmour):
        self.MobID = MobID
        self.HP = HP
        self.XP = XP
        self.ReqLevel = ReqLevel
        self.AttackType = AttackType
        self.Attack = Attack
        self.Armour = Armour
        self.MagicArmour = MagicArmour
    
    def Info(self):
        return f"HP: {self.HP}, XP: {self.XP}, Attack Type: {self.AttackType}, Attack: {self.Attack}, Armour: {self.Armour}"


class Location(Base):
    __tablename__ = "locations"

    LocationID = Column("LocationID", Integer, primary_key=True)
    XCoord = Column("XCoord", Integer)
    YCoord = Column("YCoord", Integer)
    LocationType = Column("LocationType", String)

    Items = relationship("Item", backref="location")

    def __init__(self, LocationID, XCoord, YCoord, LocationType):
        self.LocationID = LocationID
        self.XCoord = XCoord
        self.YCoord = YCoord
        self.LocationType = LocationType



class Item(Base):
    __tablename__ = 'items'

    ItemID = Column("ItemID", Integer, primary_key=True)
    ItemName = Column("ItemName", String)
    Cost = Column("Cost", Integer)
    # CostToScale = Column("CostToScale", Integer) - не нужен
    ItemType = Column("ItemType", Integer)
    HP = Column("HP", Integer)
    Magicka = Column("Magicka", Integer)
    Attack = Column("Attack", Integer)
    MagicAttack = Column("MagicAttack", Integer)
    Armour = Column("Armour", Integer)
    MagicArmour = Column("MagickArmour", Integer)
    ReqLevel = Column("ReqLevel", Integer)

    InLocationID = Column("InLocation", Integer, ForeignKey("locations.LocationID"))
    PlayersID = Column("PlayersID", Integer, ForeignKey("players.UserID"))

    Active = Column("Active", Boolean)

    def __init__(self, ItemID, ItemName, Cost, ItemType, HP, Magicka, Attack, MagicAttack, Armour, MagicArmour, ReqLevel, 
            InLocationID, PlayersID):
        self.ItemID = ItemID
        self.ItemName = ItemName
        self.Cost = Cost
        self.ItemType = ItemType
        self.HP = HP
        self.Magicka = Magicka
        self.Attack = Attack
        self.MagicAttack = MagicAttack
        self.Armour = Armour
        self.MagicArmour = MagicArmour
        self.ReqLevel = ReqLevel
        self.InLocationID = InLocationID
        self.PlayersID = PlayersID
        self.Active = False
    
    def info(self):
        if self.ItemType == "Potion":
            return f"Name: {self.ItemName}\nHP: {self.HP}\nMagicka: {self.Magicka}"
        ret = f"Name: {self.ItemName}, \nCost: {self.Cost}, Type = {self.ItemType}, HP = {self.HP}, Magicka = {self.Magicka}, Attack = {self.Attack}, Magic Attack = {self.MagicAttack}, Armour = {self.Armour}, Magic Armour = {self.MagicArmour}, Required Level = {self.ReqLevel}"
        if self.PlayersID != -1:
            ret += f"\nActive: {self.Active}"
        return ret
