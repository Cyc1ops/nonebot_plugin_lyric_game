import random
from nonebot.params import State, CommandArg, EventMessage
from nonebot.typing import T_State
from nonebot import on_command, on_regex, on_keyword, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GROUP, MessageSegment, Event, Message, GroupMessageEvent
import os
import json
import time

file = os.path.join(os.path.dirname(__file__), 'lyric.json')
song_json = {}
song_json = json.load(open(file, 'r', encoding='utf8'))
first_lyric = True
round = 5
id = 0
qid = 0
aid = 0
flag = False


game_state = {}

__help__= MessageSegment.image('https://i0.hdslb.com/bfs/album/9b38944f3e52699288f86a3ce57deb5a807c73bd.png')

open_game = on_command('歌词接龙', priority=56, block=True)

song_lib = on_command('查看曲库', priority=56, block=True)

@song_lib.handle()
async def _(bot: Bot, event: GroupMessageEvent,  args: Message = CommandArg()):
    msg = '当前曲库歌曲有：'
    for song in song_json.keys():
        msg = msg + f'\n《{song}》'
    await song_lib.finish(msg)


@open_game.handle()
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    state: T_State = State(),
    arg: Message = CommandArg(),
):
    global game_state, first_lyric, round, id, qid, aid
    msg = arg.extract_plain_text().strip()

    if msg == "帮助":
        await open_game.finish(__help__)
    elif not msg:
        all_song = list(song_json.keys())
        randid = random.randrange(len(song_json))
        song = all_song[randid]
    else:
        if msg in song_json.keys():
            song = msg
        else:
            await open_game.finish('曲库内没找到你说的歌名诶，输入“查看曲库”可以查看当前曲库内的所有歌曲')

    # game_state = {}
    init_gamer(event)


    __start__=f'歌词接龙开始！本次接龙的歌曲名字是《{song}》\n乃老师会随机唱出一句歌词，谁最先接上了后面对应的歌词谁就赢得一轮胜利，总共七轮中谁接歌词最多谁就获得最终的胜利\n倒计时三秒钟之后就开始比赛了哦，请各位准备好哦~'
    await open_game.send(__start__)
    await open_game.send('3')
    time.sleep(0.8)
    await open_game.send('2')
    time.sleep(0.8)
    await open_game.send('1')
    time.sleep(0.8)

    # game_state[event.group_id]['round'] = 7
    # game_state[event.group_id]['time'] =

    id = random.randrange(len(song_json[song]) - 1) + 1
    qid = str(id)
    aid = str(id + 1)
    await open_game.send(f'🎵{random.choice(song_json[song][qid])}🎵')
    # print(game_state)
    first_lyric = True
    lyric = on_message(block=True, temp=True)
    round = 5
    @lyric.handle()
    async def _(event: GroupMessageEvent, args: Message = EventMessage()):
        global game_state, round, first_lyric, id, qid, aid, flag
        print(game_state)
        msg = args.extract_plain_text().strip()
        if msg == '中止歌词接龙':
            await lyric.finish('歌词接龙已结束')
        if event.group_id in game_state.keys():
            # for line in song_json[song][aid]:

            # if not first_lyric:
            #     id = random.randrange(len(song_json[song]) - 1) + 1
            #     qid = str(id)
            #     aid = str(id + 1)
            #     await lyric.send(f'🎵{random.choice(song_json[song][qid])}🎵')

            for line in song_json[song][aid]:
                if msg.startswith(line):
                    flag = True
                else:
                    flag = False

            if flag and round > 0:
            # if msg.startswith(song_json[song][aid][x]):
                init_gamer(event)
                game_state[event.group_id][event.user_id]['win_count'] += 1
                round -= 1
                first_lyric = False
                id = random.randrange(len(song_json[song]) - 1) + 1
                qid = str(id)
                aid = str(id + 1)
                await lyric.send('bingo~', at_sender=True)
                await lyric.send('准备好哦,倒计时3..2..1..')
                time.sleep(2)
                await lyric.reject(f'🎵{random.choice(song_json[song][qid])}🎵')


            if flag and round <= 0:
                await lyric.send('bingo~这是最后一句歌词捏', at_sender=True)
                win, winner_id = rank(event.group_id)
                win_msg = '这场比赛结束了哦~让我们来看看最终排名吧：' + win
                await lyric.send(win_msg)
                win_name = game_state[event.group_id][winner_id]['nickname']
                winner = f'本场比赛赢家是 {win_name}' + MessageSegment.at(winner_id)
                game_state[event.group_id] = {}
                await lyric.finish(winner)
            else:
                await lyric.reject('不对哦~', at_sender=True)



def init_gamer(event: GroupMessageEvent):
    """
    初始化玩家数据
    """
    global game_state
    group_id = event.group_id
    user_id = event.user_id
    nickname = event.sender.card if event.sender.card else event.sender.nickname

    if group_id not in game_state.keys():
        game_state[group_id] = {}
    if user_id not in game_state[group_id].keys():
        game_state[group_id][user_id] = {
            "nickname": nickname,
            "win_count": 0
        }
    return game_state

def rank(group_id):
    all_gamer = list(game_state[group_id].keys())
    all_gamer_data = [game_state[group_id][x]['win_count'] for x in all_gamer]

    win_msg = ''
    for _ in range(len(all_gamer)):
        _max = max(all_gamer_data)
        _max_id = all_gamer[all_gamer_data.index(_max)]
        name = game_state[group_id][_max_id]['nickname']

        win_msg += f'\n{name}：答对{_max}次'
        if _ == 0:
            winner_id = _max_id

        all_gamer_data.remove(_max)
        all_gamer.remove((_max_id))

    return win_msg, winner_id



