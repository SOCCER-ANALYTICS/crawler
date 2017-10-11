import requests, json
#from useragent import random_agent

if __name__ == "__main__":
	url = 'https://www.whoscored.com/StatisticsFeed/1/GetPlayerStatistics'
	player_id = '23540'
	params = {
		'category': 'card',
		'subcategory': 'type',
		'statsAccumulationType': '2',
		'isCurrent': 'true',
		'playerId': player_id,
		'teamIds': '',
		'matchId': '',
		'stageId': '',
		'tournamentOptions': '',
		'sortBy': 'Rating',
		'sortAscending': '',
		'age': '',
		'ageComparisonType': '0',
		'appearances': '',
		'appearancesComparisonType': '0',
		'field': '',
		'nationality': '',
		'positionOptions': '%27FW%27,%27AML%27,%27AMC%27,%27AMR%27,%27ML%27,%27MC%27,%27MR%27,%27DMC%27,%27DL%27,%27DC%27,%27DR%27,%27GK%27,%27Sub%27',
		'timeOfTheGameEnd': '5',
		'timeOfTheGameStart': '0',
		'isMinApp': '',
		'page': '1',
		'includeZeroValues': 'true',
		'numberOfPlayersToPick': ''
	}
	proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
	
	#cookies = requests.get("https://whoscored.com", proxies=proxies).cookies
	cookies = requests.get("https://whoscored.com").cookies
	#headers = {'Content-Type': 'application/json; charset=utf-8', 'User-Agent': random_agent()}
	headers = {'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

	#response = requests.get(url, params=params, headers=headers, cookies=cookies, proxies=proxies)
	response = requests.get(url, params=params, headers=headers)
	print response.text