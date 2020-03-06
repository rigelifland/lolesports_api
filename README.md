# lolesports_api

A python library for downloading and parsing League of Legends Esports game data using the [Unofficial LoL Esports API](https://vickz84259.github.io/lolesports-api-docs/)

## Motivation
lolesports_api is designed to make it easy to calculate statistics on Esports game data. Game data is not readily available, but can be accessed with some difficulty by using the [same API which the lolesports.com livestats interface uses](https://feed.lolesports.com/livestats/v1/window/103462440145619650?startingTime=2020-02-04T02:37:50Z). This library streamlines that process and makes it easy to download all the available data for a game to a json file. Additionally, the raw data coming from the livestats API is not structured in a convenient form for performing analysis the game. This library parses the raw data into models which make accessing it simpler. 

## Usage
#### Structure
The overarching structure used by Riot's APIs is mirrored here:

    [League] > [Tournament] > [Event] > [Game] > [Team] > [Participant]

For instance:

    LCS > Spring Split 2020 > SemiFinals > Game 5 > Red > Top
    LEC > Summer Split 2019 > G2 vs FNC (round 1) > Game 1 > Blue > Jungle

#### References
The unique IDs used by Riot's APIs are also mirrored here, but additional methods are provided for accessing data using human-readable IDs such as slugs and team names.

#### Example
```python
import lolesports_api as lol
lcs = lol.League('LCS')
springSplit = lcs.getTournamentBySlug('lcs_2020_split1')
# Spring Split 2020 utilized a Bo1 format, so every time you'll want to grab the 1st game
tsm_vs_clg = springSplit.getEventByTeamGame('clg', 4).getGameByNum(1)

# The following steps will automatically be performed if the json file has already been downloaded.
tsm_vs_clg.download()
tsm_vs_clg.loadData()
tsm_vs_clg.parseData()

tsm_vs_clg.red.top.data
# returns a pandas dataframe of all data recorded by a player

```
