import requests as _requests
from datetime import datetime as _datetime, timedelta as _timedelta

def downloadDetails(game_id):
    time_format = r'%Y-%m-%dT%H:%M:%SZ'
    windowApi = f'https://feed.lolesports.com/livestats/v1/window/{game_id}'
    detailApi = f'https://feed.lolesports.com/livestats/v1/details/{game_id}'
    windowData = requests.get(windowApi).json()
    window_time = _datetime.strptime(windowData['frames'][-1]['rfc460Timestamp'].split('.')[0].split('Z')[0] + 'Z', time_format)
    # Round to the nearest 10 seconds per API requirements
    window_time = window_time - _timedelta(minutes=0, \
                                          seconds=window_time.second%10 - 10, \
                                          microseconds=window_time.microsecond)
    
    frames = windowData['frames']
    while windowData['frames'][-1]['gameState'] != 'finished':
        params = {'startingTime': window_time.strftime(time_format)}
        windowData =  _requests.get(windowApi, params=params).json()
        detailData =  _requests.get(detailApi, params=params).json()
        if windowData['frames'][-1]['rfc460Timestamp'] != frames[-1]['rfc460Timestamp']:
            for fIdx in range(len(windowData['frames'])):
                assert windowData['frames'][fIdx]['rfc460Timestamp'] == detailData['frames'][fIdx]['rfc460Timestamp']
                for pIdx in range(0, 5):
                    windowParticipant = windowData['frames'][fIdx]['blueTeam']['participants'][pIdx]
                    detailParticipant = detailData['frames'][fIdx]['participants'][pIdx]
                    assert windowParticipant['participantId'] == detailParticipant['participantId']
                    windowParticipant.update(detailParticipant)

                    windowParticipant = windowData['frames'][fIdx]['redTeam']['participants'][pIdx]
                    detailParticipant = detailData['frames'][fIdx]['participants'][pIdx+5]
                    assert windowParticipant['participantId'] == detailParticipant['participantId']
                    windowParticipant.update(detailParticipant)
            frames.extend(windowData['frames'])
        window_time = window_time + _timedelta(seconds=10)

    windowData['frames'] = frames
    return windowData

def downloadMeta(query, params={}):
    api = 'https://esports-api.lolesports.com/persisted/gw/'
    requestHeader = {
        'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z',
        'hl': 'en-US'
    }
    params['hl'] = 'en-US'
    response =  _requests.get(api + query, headers=requestHeader, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Bad Query: {response.json()}')