import logging

logger = logging.getLogger('ConfigManager')
logger.setLevel(logging.DEBUG)

class ConfigManager():
    DEFAULT_GUILD_CONFIG_VALUES = {
        '_comment_antispam': 'Antispam',
        'antispam': {
            '_comment': 'Antispam - a thing which prevents your members from spamming in chat. You can either do nothing except for saying "Stop spamming!" or timeout them. To not timeout them, set TIMEOUT_TIME to 0',
            'enabled_spam_protection': True,
            'TIME_FRAME_BETWEEN_MSGS_MAX_SECONDS': 5.0,
            'MAX_COUNT_IN_TIME_FRAME': 5,
            'TIMEOUT_TIME': 15,
            'SPAM_MESSAGE': '<@%user%> Do not spam!',
            '_comment_SPAM_MESSAGE': 'Message to send if a member spams in chat',
            '_comment_TIMEOUT_TIME': 'Timeout time on antispam trigger',
            '_comment_MAX_COUNT_IN_TIME_FRAME': 'Max messages in the time frame',
            '_comment_TIME_FRAME_BETWEEN_MSGS_MAX_SECONDS': 'Time frame to count messages in',
            '_comment_enabled_spam_protection': 'Anti-spam status (On/off)'
        },
        '_comment_modlogs': "Moderation logs",
        "modlogs": {
            "_comment": "Configure moderation logs",
            "channel": 0,
            "_comment_channel": "Channel ID to send logs to, set to 0 to disable"
        },
        '_comment_ch': "Channel settings",
        "ch": {
            "_comment": "Setup your channels here",
            "wel-channel": 0,
            "_comment_wel-channel": "Channel ID to welcome members, set to 0 to disable",
            "lea-channel": 0,
            "_comment_lea-channel": "Channel ID to bye members, setto 0 to disable"
        },
        '_comment_abuse': "Abusing Protection",
        "abuse": {
               "_comment": "Abusing Protection - This Helps you are your server to get help from abusers [Note: Our coders didn't write all abusing words they written some of them]",
               "enable_abuse_protection": True,
               "TIMEOUT_TIME": 15,
               "ABUSE_MESSAGE": "<@%user%> Do Not Abuse",
               "_comment_TIMEOUT_TIME": "Timeout time on abuse trigger",
               "_comment_ABUSE_MESSAGE": "Message to send if member abuse in chat",
               "_comment_enable_abuse_protection": "Abuse Protection Status (On/Off)"
        }
    }

    DEFAULT_USER_CONFIG_VALUES = {
        
    }
    
    def __init__(self, guilds, users):
        self.guilds = guilds
        self.users = users

    def getGuildConfigValue(self, id: int, value: str):
        guildConfig = self.guilds.find_one({
            'guild_id': id
        })
        if not guildConfig:
            guildConfig = self.DEFAULT_GUILD_CONFIG_VALUES.copy()
            guildConfig['guild_id'] = id
            self.guilds.insert_one(guildConfig)
        if value == '':
            return guildConfig
        path = value.split('.')
        logger.debug('Path to config value: ' + str(path))
        value = None
        valueInDefault = None
        for s in path:
            logger.info('Value (before iteration): ' + str(value))
            logger.debug('Key: ' + s)
            if not valueInDefault:
                valueInDefault = self.DEFAULT_GUILD_CONFIG_VALUES.get(s, None)
                if not valueInDefault:
                    return None
            elif type(valueInDefault) == dict:
                if not s in valueInDefault.keys():
                    return None
                valueInDefault = valueInDefault.get(s)
            if not value:
                value = guildConfig.get(s, None)
                g = 0
            else:
                value = value.get(s, None)
                g = 1
            if type(value) == None:
                if g == 0:
                    value = guildConfig.get(s, None)
                else:
                    value = value.get(s, None)
                del g
                if not value:
                    return None
        return value

    def setGuildConfigValue(self, id: int, value: str, newValue: str):
        guildConfig = self.guilds.find_one({
            'guild_id': id
        })
        if not guildConfig:
            guildConfig = self.DEFAULT_GUILD_CONFIG_VALUES.copy()
            guildConfig['guild_id'] = id
            self.guilds.insert_one(guildConfig)
        if value == '':
            return guildConfig
        path = value.split('.')
        logger.debug('Path to config value: ' + str(path))
        value = None
        value2 = None
        valueInDefault = None
        key = None
        for s in path:
            value2 = value
            key = s
            logger.info('Value (before iteration): ' + str(value))
            logger.debug('Key: ' + s)
            if not valueInDefault:
                valueInDefault = self.DEFAULT_GUILD_CONFIG_VALUES.get(s, None)
                if not valueInDefault:
                    return None
            elif type(valueInDefault) == dict:
                if not s in valueInDefault.keys():
                    return None
                valueInDefault = valueInDefault.get(s)
            if not value:
                value = guildConfig.get(s, None)
                g = 0
            else:
                value = value.get(s, None)
                g = 1
            if type(value) == None:
                if g == 0:
                    value = guildConfig.get(s, None)
                else:
                    value = value.get(s, None)
                del g
                if not value:
                    return None
        value2[key] = newValue
        logger.info('Saving config...')
        self.guilds.find_one_and_delete({
            'guild_id': id
        })
        self.guilds.insert_one(guildConfig)
    def upgradeGuildConfig(self, id: int, guildConfig = None, defaultConfig = DEFAULT_GUILD_CONFIG_VALUES, save = False):
        """Upgrade guild config in case some changes happen"""
        if not guildConfig:
            guildConfig = self.DEFAULT_GUILD_CONFIG_VALUES.copy()
            guildConfig['guild_id'] = id
        logger.info("Upgrading guild config")
        for key in defaultConfig.keys():
            if key == 'guild_id':
                continue
            logger.info(f'Current key: {key}')
            element = defaultConfig[key]
            if type(element) == dict:
                logger.info('Detected dict')
                if not key in guildConfig.keys() or type(guildConfig[key]) != dict:
                    guildConfig[key] = element
                else:
                    logger.info('Running the function recursively...')
                    guildConfig[key] = self.upgradeGuildConfig(id, guildConfig[key], self.DEFAULT_GUILD_CONFIG_VALUES[key])
            else:
                # Don't touch if the value already exists
                print(guildConfig)
                if not key in guildConfig.keys():
                    logger.info(f'Added a key which didn\'t existed: {key}')
                    guildConfig[key] = element
        # Remove values which were removed from default guild config
        newGuildConfig = {}
        for key in guildConfig.keys():
            if key not in defaultConfig.keys() and key != 'guild_id' and key != '_id': # Make sure it won't delete Discord or MongoDB-assigned server ID
                logger.warn(f'Removed key {key} because it was been removed from the default config')
            else:
                if key.startswith('_comment'):
                    newGuildConfig[key] = defaultConfig[key]
                else:
                    newGuildConfig[key] = guildConfig[key]
        logger.info('Finished upgrading config')
        if save:
            logger.info('Saving config...')
            self.guilds.find_one_and_delete({
                'guild_id': id
            })
            self.guilds.insert_one(newGuildConfig)
        return newGuildConfig
    def getUserConfigValue(self, id: int, value: str):
        # Nothing in the user config so it's not implemented
        logger.error("Nothing in the user config, so user config is not implemented. Tho it's called somewhere, please don't call this or ask ModGog Team to add user config!")
        return None
