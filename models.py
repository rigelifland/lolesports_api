from lolesports_api.downloaders import downloadMeta, downloadDetails
import glob as _glob
import json as _json
import os as _os
import numpy as _np
import pandas as _pd

def dictToAttr(self, dict):
    for key, value in dict.items():
        setattr(self, key, value)


class League():
    def __init__(self, leagueSlug):
        self.slug = leagueSlug

        queryData = downloadMeta('getLeagues')
        self.data = [league for league in queryData['data']['leagues'] if league['slug'] == leagueSlug][0]
        dictToAttr(self, self.data)

        queryData = downloadMeta('getTournamentsForLeague', {'leagueId': self.id})
        self.tournaments = queryData['data']['leagues'][0]['tournaments']
    
    def getTournament(self, tournamentId):
        tournamentData = [t for t in self.tournaments if t['id'] == tournamentId][0]
        return Tournament(self.id, tournamentId, tournamentData=tournamentData)

    def getTournamentBySlug(self, tournamentSlug):
        tournamentData = [t for t in self.tournaments if t['slug'] == tournamentSlug][0]
        return Tournament(self.id, tournamentSlug, tournamentData=tournamentData)

    def download(self, folder='.', **kwargs):
        folder = f'{folder}/{self.slug}'
        _os.makedirs(folder, exist_ok=True)
        for tournamentSlug in [t['slug'] for t in self.tournaments]:
            split = self.getTournament(tournamentSlug)
            split.download(folder=folder, **kwargs)


class Tournament():
    def __init__(self, leagueId, tournamentId, tournamentData=[]):
        self.leagueId = leagueId
        self.id = tournamentId

        if not tournamentData:
            queryData = downloadMeta('getTournamentsForLeague', {'leagueId': leagueId})
            tournamentData = [t for t in queryData['data']['leagues'][0]['tournaments'] if t['id'] == self.id][0]
        self.data = tournamentData
        dictToAttr(self, self.data)

        queryData = downloadMeta('getCompletedEvents', {'tournamentId': self.id})
        self.events = queryData['data']['schedule']['events']

    def getEvent(self, eventId):
        return Event(self.id, eventId)

    def getEventByTeamGame(self, teamSlug, gameNum):
        teamEvents = [event for event in self.events if teamSlug.lower() in \
                [team['code'].lower() for team in event['match']['teams']]]
        assert gameNum <= len(teamEvents), "Team hasn't played that many games!"
        return self.getEvent(teamEvents[gameNum-1]['match']['id'])

    def download(self, folder='.', **kwargs):
        folder = f'{folder}/{self.slug}'
        _os.makedirs(folder, exist_ok=True)
        for eventId in [e['match']['id'] for e in self.events]:
            event = self.getEvent(eventId)
            event.download(folder=folder, **kwargs)


class Event():
    def __init__(self, tournamentId, eventId):
        self.tournamentId = tournamentId
        self.id = eventId

        queryData = downloadMeta('getEventDetails', {'id': eventId})
        self.data = queryData['data']['event']
        dictToAttr(self, self.data)

        self.games = self.data['match']['games']

    def getGame(self, gameId):
        gameData = {
            'winner': [team['name'] for team in self.data['match']['teams'] if team['result']['gameWins'] == 1][0],
            'teams': self.data['match']['teams']            
        }
        return Game(self.id, gameId, gameData)

    def getGameByNum(self, gameNum):
        gameId = [game['id'] for game in self.games if game['number'] == gameNum][0]
        return self.getGame(gameId)
    
    def download(self, **kwargs):
        for gameId in [g['id'] for g in self.games]:
            game = self.getGame(gameId)
            game.download(**kwargs)


class Game():
    def __init__(self, eventId, gameId, gameData=[], autoLoad=True):
        self.eventId = eventId
        self.id = gameId

        if not gameData:
            queryData = downloadMeta('getEventDetails', {'id': eventId})
            teamData = queryData['data']['event']['match']['teams']
            gameData = {
                'winner': [team['name'] for team in teamData if team['result']['gameWins'] == 1][0],
                'teams': teamData            
            }
        dictToAttr(self, gameData)
        
        if autoLoad:
            try:
                self.loadData()
                self.parseData()
            except AssertionError:
                pass

    def download(self, folder='.', verbose=True, overwrite=False):
        try:
            fname = f'{folder}/{self.id}.json'
            if (not _os.path.isfile(fname)) or (overwrite):
                gameData = downloadDetails(self.id)
                with open(fname, 'w') as fp:
                    _json.dump(gameData, fp)
                if verbose:
                    print(f'Finished writing to {fname}')
            else:
                if verbose:
                    print(f'Already exists. Skipping {self.id}')
        except Exception as e:
            print(f'Failed to download {self.id}.')
            print(e)

    def loadData(self):
        fname = _glob.glob(f'*/*/{self.id}.json')
        assert len(fname) > 0, 'No game data file found!'
        assert len(fname) < 2, f'Multiple game data files found: {fname}'            
        with open(fname[0], 'r') as f:
            gameData = _json.load(f)
        self.json = gameData
        self._filename = fname[0]

    def parseData(self):
        ## Parse Time
        time = _np.array([frame['rfc460Timestamp'][:-1] for frame in self.json['frames']], dtype=_np.datetime64)
        # time is seconds since the SECOND timestamp. I believe the first timestamp is when they start loading in...
        time = (time - time[1])/_np.timedelta64(1, 's')
        pauseIdxs = [idx for idx, frame in enumerate(self.json['frames']) if frame['gameState']=='paused']
        for pIdx in pauseIdxs:
            time[pIdx+1:] -= time[pIdx+1] - time[pIdx]
        self._timeIndex = _pd.TimedeltaIndex(time)

        
        self.red = Team(self, 'red')
        self.blue = Team(self, 'blue')

        self.frames = self.json['frames']


class Team():
    def __init__(self, game, side):
        self._game = game
        self._side = side


        self.data = _pd.DataFrame([frame[side + 'Team'] for frame in game.json['frames']])

        self.top = Participant(self, 'top')
        self.jungle = Participant(self, 'jungle')
        self.mid = Participant(self, 'mid')
        self.bottom = Participant(self, 'bottom')
        self.support = Participant(self, 'support')

        self.data.drop(columns='participants')
   

class Participant():
    def __init__(self, team, role):
        teamParticipantData = team._game.json['gameMetadata'][team._side+'TeamMetadata']['participantMetadata']
        participantData = [p for p in teamParticipantData if p['role'] == role][0]
        self.data = _pd.DataFrame(
            [[pFrame for pFrame in pGroup if pFrame['participantId'] == participantData['participantId']][0] 
                for pGroup in team.data['participants']])
        dictToAttr(self, participantData)