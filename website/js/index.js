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
    let gameIdStr = JSON.stringify(gameState.id)
    let gamePlayersStr = JSON.stringify(gameState.players)
    let gameStatusStr = JSON.stringify(gameState.status)
    let gameHostStr = JSON.stringify(gameState.hostId)
    let gameStr = JSON.stringify(gameState)
    $('div#game.game-view>p#state').text("Номер комнаты: " + gameIdStr + " ИГРОКИ: " + gamePlayersStr + " Статус: " + gameStatusStr + " Хост: " + gameHostStr)
    //$('div#game.game-view>p#state').text(gameState)
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
			switchToView('choose-game-type')
		}
	)
}

function createGame() {
	let url = getMethodUrl('/games/create')
    let token = getToken()
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

function leaveGame() {
	let url = getMethodUrl('/games/leave')
    $.get(
        url,
        {
            authToken: getToken(),
        }, 
        function(data) {
            switchToView('choose-game-type')
        }
    )
}

function startGame() {
	let url = getMethodUrl('/games/start')
    $.get(
        url,
        {
            authToken: getToken(),
        }, 
        function(data) {
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

function move(){
	switchToView('join-game')
}

/*==========[Logic]==========*/

function init() {
	setApiUrl('http://localhost/api')
	switchToView('login')
}

$(document).ready(function() {
	init()

	$('#btn-login').click(login)
	$('#btn-create').click(createGame)
	$('#btn-join').click(joinGame)
	$('#btn-choose-type').click(move)
    $('#btn-leave').click(leaveGame)
    $('#btn-start').click(startGame)
	setInterval(updateGameState, 1000)
})
