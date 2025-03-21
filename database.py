import os, sys, random, datetime, json, copy
from models import *

class DataStore:
    file = "datastore.json"
    system: dict = {}
    
    @staticmethod
    def setup(withSystemMetadata=False) -> bool:
        if not os.path.isfile(os.path.join(os.getcwd(), DataStore.file)):
            try:
                with open(DataStore.file, "w") as f:
                    json.dump({}, f)
            except Exception as e:
                Logger.log("DATASTORE SETUP ERROR: Failed to setup DataStore file. Error: {}".format(e))
                return False
        
        if withSystemMetadata:
            DataStore.system = DataStore.readFragment("system")
            if DataStore.system == None:
                DataStore.writeFragment("system", {})
                DataStore.system = {}
        
        return True
    
    @staticmethod
    def writeFragment(id: str, data: dict) -> bool:
        try:
            store = None
            with open(DataStore.file, "r+") as f:
                store = json.load(f)
            
            store[id] = data
            
            with open(DataStore.file, "w") as f:
                json.dump(store, f)
            
            return True
        except Exception as e:
            Logger.log("DATASTORE WRITEFRAGMENT ERROR: Failed to write fragment to DataStore file. Error: {}".format(e))
            return False
    
    @staticmethod
    def readFragment(id: str) -> dict | None:
        try:
            store = None
            with open(DataStore.file, "r") as f:
                store = json.load(f)
                if id not in store:
                    Logger.log("DATASTORE READFRAGMENT WARNING: Fragment with ID '{}' not found in DataStore file.".format(id))
                    return None
                
            return store[id]
        except Exception as e:
            Logger.log("DATASTORE READFRAGMENT ERROR: Failed to read fragment from DataStore file. Error: {}".format(e))
            return None
    
    @staticmethod
    def destroyFragment(id: str) -> bool:
        try:
            store = None
            with open(DataStore.file, "r+") as f:
                store = json.load(f)
                if id not in store:
                    Logger.log("DATASTORE DESTROYFRAGMENT WARNING: Fragment with ID '{}' not found in DataStore file.".format(id))
                    return True
            
            del store[id]
            
            with open(DataStore.file, "w") as f:
                json.dump(store, f)
            
            return True
        except Exception as e:
            Logger.log("DATASTORE DESTROYFRAGMENT ERROR: Failed to destroy fragment in DataStore file. Error: {}".format(e))
            return False
    
    @staticmethod
    def wipe() -> bool:
        try:
            with open(DataStore.file, "w") as f:
                json.dump({}, f)
            
            return True
        except Exception as e:
            Logger.log("DATASTORE WIPE ERROR: Failed to wipe DataStore file. Error: {}".format(e))
            return False
    
    @staticmethod
    def loadSystemMetadata() -> None:
        DataStore.system = DataStore.readFragment("system")
        if DataStore.system == None:
            DataStore.writeFragment("system", {})
            DataStore.system = {}
        
        return
    
    @staticmethod
    def writeSystemMetadata() -> bool:
        return DataStore.writeFragment("system", DataStore.system)
    
    @staticmethod
    def rawLoad() -> dict:
        if os.path.isfile(os.path.join(os.getcwd(), DataStore.file)):
            with open(DataStore.file, "r") as f:
                return json.load(f)
        else:
            return {}