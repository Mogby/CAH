/*==========[State]==========*/

var State = {}

function setToken(token) {
	State.token = token
}

function getToken() {
	return State.token
}

function setGameId(gameId) {
	State.gameId = gameId
}

function getGameId() {
	return State.gameId
}

function setApiUrl(apiUrl) {
	State.apiUrl = apiUrl
}

function getMethodUrl(method) {
	return State.apiUrl + method
}

function switchToView(newView) {
	let currentView = State.currentView
	if (currentView !== undefined) {
		$(`div#${currentView}.game-view`).fadeOut()
	}
	$(`div#${newView}.game-view`).fadeIn()
	State.currentView = newView
}

function displayGameState(gameState) {
	let gameStateStr = JSON.stringify(gameState)
	$('div#game.game-view>p#state').text(gameStateStr)
}

/*==========[API]==========*/

function login() {
	let name = $('input#login').val()

	let url = getMethodUrl('/players/add')
	$.get(
		url,
		{ name: name },
		function(data) {
			setToken(data)
			switchToView('join-game')
		}
	)
}

function createGame() {
	let url = getMethodUrl('/games/create')
	$.get(
		url,
		{ authToken: getToken() },
		function(data) {
			setGameId(data)
			switchToView('game')
		}
	)
}

function joinGame() {
	let gameId = $('input#game-id').val()
	let token = getToken()

	let url = getMethodUrl('/games/join')
	$.get(
		url,
		{
			id: gameId,
			authToken: token
		},
		function(data) {
			setGameId(gameId)
			switchToView('game')
		}
	)
}

function updateGameState() {
	let gameId = getGameId()
	let token = getToken()

	if (gameId === undefined || token === undefined) {
		return
	}

	let url = getMethodUrl('/games/get')
	$.get(
		url,
		{
			id: gameId,
			authToken: token
		},
		function(gameState) {
			displayGameState(gameState)
		}
	)
}

/*==========[Logic]==========*/

function init() {
	setApiUrl('http://localhost:8000')
	switchToView('login')
}

$(document).ready(function() {
	init()

	$('#btn-login').click(login)
	$('#btn-create').click(createGame)
	$('#btn-join').click(joinGame)

	setInterval(updateGameState, 1000)
})