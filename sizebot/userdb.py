import json

from sizebot.conf import conf
from sizebot.digidecimal import Decimal
from sizebot import digierror as errors
from sizebot.digiSV import infinitySV, infinityWV
from sizebot import utils

# Defaults
defaultheight = Decimal("1.754")  # meters
defaultweight = Decimal("66760")  # grams

# Map the deprecated user array constants to the new names
#                      NICK        DISP       CHEI      BHEI          BWEI          UNIT          SPEC
DEPRECATED_NAME_MAP = ["nickname", "display", "height", "baseheight", "baseweight", "unitsystem", "species"]


class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id", "nickname", "display", "_height", "_baseheight", "_baseweight", "_unitsystem", "species"]

    def __init__(self):
        self.id = None
        self.nickname = None
        self.display = True
        self._height = defaultheight
        self._baseheight = defaultheight
        self._baseweight = defaultweight
        self._unitsystem = "m"
        self.species = None

    def __str__(self):
        return f"ID {self.id}, NICK {self.nickname}, DISP {self.display}, CHEI {self.height}, BHEI {self.baseheight}, BWEI {self.baseweight}, UNIT {self.unitsystem}, SPEC {self.species}"

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = utils.clamp(0, Decimal(value), infinitySV)

    @property
    def baseheight(self):
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value):
        self._baseheight = utils.clamp(0, Decimal(value), infinitySV)

    @property
    def baseweight(self):
        return self._baseweight

    @baseweight.setter
    def baseweight(self, value):
        self._baseweight = utils.clamp(0, Decimal(value), infinityWV)

    # Check that unitsystem is valid and lowercase
    @property
    def unitsystem(self):
        return self._unitsystem

    @unitsystem.setter
    def unitsystem(self, value):
        value = value.lower()
        if value not in ["m", "u"]:
            raise ValueError(f"Invalid unitsystem: '{value}'")
        self._unitsystem = value

    @property
    def tag(self):
        if self.id is not None:
            tag = f"<@{self.id}>"
        else:
            tag = self.nickname
        return tag

    # Act like an array for legacy usage

    def __getitem__(self, key):
        attrname = DEPRECATED_NAME_MAP[key]
        return getattr(self, attrname)

    def __setitem__(self, key, value):
        attrname = DEPRECATED_NAME_MAP[key]
        return setattr(self, attrname, value)

    # Return an python dictionary for json exporting
    def toJSON(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "display": self.display,
            "height": str(self.height),
            "baseheight": str(self.baseheight),
            "baseweight": str(self.baseweight),
            "unitsystem": self.unitsystem,
            "species": self.species
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.id = jsondata["id"]
        userdata.nickname = jsondata["nickname"]
        userdata.display = jsondata["display"]
        userdata.height = Decimal(jsondata["height"])
        userdata.baseheight = Decimal(jsondata["baseheight"])
        userdata.baseweight = Decimal(jsondata["baseweight"])
        userdata.unitsystem = jsondata["unitsystem"]
        userdata.species = jsondata["species"]
        return userdata


def getuserpath(userid):
    return conf.userdbpath / f"{userid}.json"


def save(userdata):
    userid = userdata.id
    if userid is None:
        raise errors.CannotSaveWithoutIDException
    conf.userdbpath.mkdir(exist_ok = True)
    jsondata = userdata.toJSON()
    with open(getuserpath(userid), "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(userid):
    try:
        with open(getuserpath(userid), "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException
    return User.fromJSON(jsondata)


def delete(userid):
    getuserpath(userid).unlink(missing_ok = True)


def exists(userid):
    exists = True
    try:
        load(userid)
    except errors.UserNotFoundException:
        exists = False
    return exists


def count():
    usercount = len(list(conf.userdbpath.glob("*.json")))
    return usercount
