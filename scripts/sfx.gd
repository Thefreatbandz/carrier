extends Node
## Sfx: pooled one-shot sound effects, callable anywhere as Sfx.play("hit").

var _players: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _idx := 0

const NAMES := ["swing", "hit", "die", "pickup", "surge", "frenzy", "sense",
	"extract_tick", "upgrade", "hurt", "turn", "levelup", "click"]

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for n in NAMES:
		_streams[n] = load("res://assets/audio/%s.wav" % n) as AudioStream
	for i in range(10):
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)

func play(n: String, pitch := 1.0) -> void:
	if not _streams.has(n) or _streams[n] == null:
		return
	var p := _players[_idx]
	_idx = (_idx + 1) % _players.size()
	p.stream = _streams[n]
	p.pitch_scale = pitch * randf_range(0.94, 1.06)
	p.play()
