###############################################################################
#  Copyright (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking
#  email: lipku@foxmail.com
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

# server.py
from flask import Flask, render_template,send_from_directory,request, jsonify
from flask_sockets import Sockets
import base64
import json
#import gevent
#from gevent import pywsgi
#from geventwebsocket.handler import WebSocketHandler
import re
import numpy as np
from threading import Thread,Event
#import multiprocessing
import torch.multiprocessing as mp

from aiohttp import web
import aiohttp
import aiohttp_cors
from aiortc import RTCPeerConnection, RTCSessionDescription,RTCIceServer,RTCConfiguration
from aiortc.rtcrtpsender import RTCRtpSender
from webrtc import HumanPlayer
from basereal import BaseReal
from llm import llm_response

import argparse
import os
import random
import shutil
import asyncio
import torch
from typing import Dict
from logger import logger
import gc

# Project root (directory containing app.py) - paths are relative to this so they work from any CWD
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Message returned when model files are missing (server runs but digital human disabled)
NO_MODEL_MSG = (
    "Model files not loaded. Add models/wav2lip256.pth and data/avatars/wav2lip256_avatar1/ then restart. See SETUP_MODELS.md."
)
# Message when model file exists but load failed (e.g. wrong checkpoint architecture)
MODEL_LOAD_FAILED_MSG = (
    "Wrong checkpoint: this code needs the wav2lip256 model from the project's folder, not standard Wav2Lip. "
    "Download wav2lip256.pth from https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ "
    "(same folder as the avatar), put it in models/wav2lip256.pth, then restart."
)

# Actual message returned to client when model unavailable (NO_MODEL_MSG or MODEL_LOAD_FAILED_MSG)
no_model_message = NO_MODEL_MSG
# Reason for no-model (so client can show hint): "files_missing" | "load_failed" | None
no_model_reason = None

app = Flask(__name__)
#sockets = Sockets(app)
nerfreals:Dict[int, BaseReal] = {} #sessionid:BaseReal
opt = None
model = None
avatar = None
        

#####webrtc###############################
pcs = set()

def randN(N)->int:
    '''生成长度为 N的随机数 '''
    min = pow(10, N - 1)
    max = pow(10, N)
    return random.randint(min, max - 1)

def build_nerfreal(sessionid:int)->BaseReal:
    opt.sessionid=sessionid
    if opt.model == 'wav2lip':
        from lipreal import LipReal
        nerfreal = LipReal(opt,model,avatar)
    elif opt.model == 'musetalk':
        from musereal import MuseReal
        nerfreal = MuseReal(opt,model,avatar)
    # elif opt.model == 'ernerf':
    #     from nerfreal import NeRFReal
    #     nerfreal = NeRFReal(opt,model,avatar)
    elif opt.model == 'ultralight':
        from lightreal import LightReal
        nerfreal = LightReal(opt,model,avatar)
    return nerfreal

def _no_model_json():
    """503 body when model not loaded; include port and reason so user can tell which server and why."""
    body = {"error": no_model_message}
    if opt is not None:
        body["port"] = getattr(opt, "listenport", None)
    if no_model_reason:
        body["reason"] = no_model_reason
    return body

#@app.route('/offer', methods=['POST'])
async def offer(request):
    def err_response(msg):
        return web.Response(status=503, content_type="application/json", text=json.dumps({"error": msg}))
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        # if len(nerfreals) >= opt.max_session:
        #     logger.info('reach max session')
        #     return web.Response(...)
        sessionid = randN(6)
        nerfreals[sessionid] = None
        logger.info('sessionid=%d, session num=%d',sessionid,len(nerfreals))
        nerfreal = await asyncio.get_event_loop().run_in_executor(None, build_nerfreal,sessionid)
        nerfreals[sessionid] = nerfreal

        ice_server = RTCIceServer(urls='stun:stun.miwifi.com:3478')
        pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[ice_server]))
        pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                pcs.discard(pc)
                del nerfreals[sessionid]
            if pc.connectionState == "closed":
                pcs.discard(pc)
                del nerfreals[sessionid]

        player = HumanPlayer(nerfreals[sessionid])
        # Match client order: client addTransceiver('video') then addTransceiver('audio'), so add video first
        video_sender = pc.addTrack(player.video)
        audio_sender = pc.addTrack(player.audio)
        capabilities = RTCRtpSender.getCapabilities("video")
        preferences = list(filter(lambda x: x.name == "H264", capabilities.codecs))
        preferences += list(filter(lambda x: x.name == "VP8", capabilities.codecs))
        preferences += list(filter(lambda x: x.name == "rtx", capabilities.codecs))
        transceiver = pc.getTransceivers()[0]  # video is first
        transceiver.setCodecPreferences(preferences)

        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "sessionid":sessionid}
            ),
        )
    except Exception as e:
        logger.exception("offer handler error")
        msg = no_model_message if getattr(opt, 'no_model', False) else ("Server error: " + str(e)[:200])
        return err_response(msg)

async def human(request):
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        params = await request.json()

        sessionid = params.get('sessionid',0)
        if sessionid not in nerfreals:
            return web.Response(status=400, content_type="application/json", text=json.dumps({
                "error": "Session expired or invalid. Click Start to connect, then try Send again."
            }))
        if params.get('interrupt'):
            nerfreals[sessionid].flush_talk()

        if params['type']=='echo':
            nerfreals[sessionid].put_msg_txt(params['text'])
        elif params['type']=='chat':
            asyncio.get_event_loop().run_in_executor(None, llm_response, params['text'],nerfreals[sessionid])                         
            #nerfreals[sessionid].put_msg_txt(res)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": 0, "msg":"ok"}
            ),
        )
    except Exception as e:
        logger.exception('exception:')
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": -1, "msg": str(e)}
            ),
        )

async def interrupt_talk(request):
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        params = await request.json()

        sessionid = params.get('sessionid',0)
        if sessionid not in nerfreals:
            return web.Response(status=400, content_type="application/json", text=json.dumps({
                "error": "Session expired or invalid. Click Start to reconnect."
            }))
        nerfreals[sessionid].flush_talk()
        
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": 0, "msg":"ok"}
            ),
        )
    except Exception as e:
        logger.exception('exception:')
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": -1, "msg": str(e)}
            ),
        )

async def humanaudio(request):
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        form= await request.post()
        sessionid = int(form.get('sessionid',0))
        if sessionid not in nerfreals:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        fileobj = form["file"]
        filename=fileobj.filename
        filebytes=fileobj.file.read()
        nerfreals[sessionid].put_audio_file(filebytes)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": 0, "msg":"ok"}
            ),
        )
    except Exception as e:
        logger.exception('exception:')
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": -1, "msg": str(e)}
            ),
        )

async def set_audiotype(request):
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        params = await request.json()

        sessionid = params.get('sessionid',0)
        if sessionid not in nerfreals:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        nerfreals[sessionid].set_custom_state(params['audiotype'],params['reinit'])

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": 0, "msg":"ok"}
            ),
        )
    except Exception as e:
        logger.exception('exception:')
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": -1, "msg": str(e)}
            ),
        )

async def record(request):
    try:
        if getattr(opt, 'no_model', False) or model is None:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        params = await request.json()

        sessionid = params.get('sessionid',0)
        if sessionid not in nerfreals:
            return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
        if params['type']=='start_record':
            # nerfreals[sessionid].put_msg_txt(params['text'])
            nerfreals[sessionid].start_recording()
        elif params['type']=='end_record':
            nerfreals[sessionid].stop_recording()
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": 0, "msg":"ok"}
            ),
        )
    except Exception as e:
        logger.exception('exception:')
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"code": -1, "msg": str(e)}
            ),
        )

async def is_speaking(request):
    if getattr(opt, 'no_model', False) or model is None:
        return web.Response(status=503, content_type="application/json", text=json.dumps(_no_model_json()))
    params = await request.json()

    sessionid = params.get('sessionid',0)
    if sessionid not in nerfreals:
        return web.Response(status=400, content_type="application/json", text=json.dumps(
            {"error": "Session expired or invalid. Click Start to reconnect."}
        ))
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"code": 0, "data": nerfreals[sessionid].is_speaking()}
        ),
    )


async def status(request):
    """GET /status: report whether model is loaded and which port we're on (to debug 503 / wrong port)."""
    model_loaded = not (getattr(opt, "no_model", False) or model is None)
    return web.Response(
        content_type="application/json",
        text=json.dumps({"model_loaded": model_loaded, "port": getattr(opt, "listenport", None)}),
    )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

async def post(url,data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url,data=data) as response:
                return await response.text()
    except aiohttp.ClientError as e:
        logger.info(f'Error: {e}')

async def run(push_url,sessionid):
    nerfreal = await asyncio.get_event_loop().run_in_executor(None, build_nerfreal,sessionid)
    nerfreals[sessionid] = nerfreal

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    player = HumanPlayer(nerfreals[sessionid])
    audio_sender = pc.addTrack(player.audio)
    video_sender = pc.addTrack(player.video)

    await pc.setLocalDescription(await pc.createOffer())
    answer = await post(push_url,pc.localDescription.sdp)
    await pc.setRemoteDescription(RTCSessionDescription(sdp=answer,type='answer'))
##########################################
# os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'
# os.environ['MULTIPROCESSING_METHOD'] = 'forkserver'                                                    
if __name__ == '__main__':
    mp.set_start_method('spawn')
    parser = argparse.ArgumentParser()
    
    # audio FPS
    parser.add_argument('--fps', type=int, default=50, help="audio fps,must be 50")
    # sliding window left-middle-right length (unit: 20ms)
    parser.add_argument('-l', type=int, default=10)
    parser.add_argument('-m', type=int, default=8)
    parser.add_argument('-r', type=int, default=10)

    parser.add_argument('--W', type=int, default=450, help="GUI width")
    parser.add_argument('--H', type=int, default=450, help="GUI height")

    #musetalk opt
    parser.add_argument('--avatar_id', type=str, default='wav2lip256_avatar1', help="define which avatar in data/avatars")
    #parser.add_argument('--bbox_shift', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=16, help="infer batch")

    parser.add_argument('--customvideo_config', type=str, default='', help="custom action json")

    parser.add_argument('--tts', type=str, default='edgetts', help="tts service type") #xtts gpt-sovits cosyvoice fishtts tencent doubao indextts2 azuretts
    parser.add_argument('--REF_FILE', type=str, default="zh-CN-YunxiaNeural",help="参考文件名或语音模型ID，默认值为 edgetts的语音模型ID zh-CN-YunxiaNeural, 若--tts指定为azuretts, 可以使用Azure语音模型ID, 如zh-CN-XiaoxiaoMultilingualNeural")
    parser.add_argument('--REF_TEXT', type=str, default=None)
    parser.add_argument('--TTS_SERVER', type=str, default='http://127.0.0.1:9880') # http://localhost:9000
    # parser.add_argument('--CHARACTER', type=str, default='test')
    # parser.add_argument('--EMOTION', type=str, default='default')

    parser.add_argument('--model', type=str, default='wav2lip') #musetalk wav2lip ultralight

    parser.add_argument('--transport', type=str, default='rtcpush') #webrtc rtcpush virtualcam
    parser.add_argument('--push_url', type=str, default='http://localhost:1985/rtc/v1/whip/?app=live&stream=livestream') #rtmp://localhost/live/livestream

    parser.add_argument('--max_session', type=int, default=1)  #multi session count
    parser.add_argument('--listenport', type=int, default=8010, help="web listen port")
    parser.add_argument('--no_model', action='store_true', help="start server without loading model (digital human disabled)")

    opt = parser.parse_args()
    os.chdir(PROJECT_ROOT)  # so all relative paths (models/, data/avatars/, lipreal, etc.) resolve correctly
    #app.config.from_object(opt)
    #print(app.config)
    opt.customopt = []
    if opt.customvideo_config!='':
        with open(opt.customvideo_config,'r') as file:
            opt.customopt = json.load(file)

    # Check if model files exist; if not, start server without model (no-model mode)
    # Use PROJECT_ROOT so paths work regardless of current working directory
    model_path = os.path.join(PROJECT_ROOT, "models", "wav2lip256.pth")
    avatar_dir = os.path.join(PROJECT_ROOT, "data", "avatars", opt.avatar_id)
    if opt.model == 'wav2lip' and not opt.no_model:
        if not os.path.isfile(model_path) or not os.path.isdir(avatar_dir):
            opt.no_model = True
            no_model_reason = "files_missing"
            logger.warning(
                "Model files missing. Server will start but digital human disabled. Add models/wav2lip256.pth and data/avatars/%s (checked %s, %s)",
                opt.avatar_id, model_path, avatar_dir
            )
        else:
            logger.info("Model/avatar paths OK: %s, %s", model_path, avatar_dir)
    elif opt.model == 'musetalk':
        if not os.path.isdir(avatar_dir) or not os.path.isfile(os.path.join(avatar_dir, "coords.pkl")):
            opt.no_model = True
            logger.warning("Avatar data missing. Server will start but digital human disabled. Add data/avatars/%s", opt.avatar_id)
    elif opt.model == 'ultralight':
        if not os.path.isdir(avatar_dir):
            opt.no_model = True
            logger.warning("Avatar data missing. Server will start but digital human disabled.")

    if not opt.no_model:
        try:
            # if opt.model == 'ernerf':       
            #     from nerfreal import NeRFReal,load_model,load_avatar
            #     model = load_model(opt)
            #     avatar = load_avatar(opt) 
            if opt.model == 'musetalk':
                from musereal import MuseReal,load_model,load_avatar,warm_up
                logger.info(opt)
                model = load_model()
                avatar = load_avatar(opt.avatar_id) 
                warm_up(opt.batch_size,model)      
            elif opt.model == 'wav2lip':
                from lipreal import LipReal,load_model,load_avatar,warm_up
                logger.info(opt)
                model = load_model(os.path.join(PROJECT_ROOT, "models", "wav2lip256.pth"))
                avatar = load_avatar(opt.avatar_id)
                warm_up(opt.batch_size,model,256)
                logger.info("Model loaded: YES (wav2lip + %s). Avatar will be available.", opt.avatar_id)
            elif opt.model == 'ultralight':
                from lightreal import LightReal,load_model,load_avatar,warm_up
                logger.info(opt)
                model = load_model(opt)
                avatar = load_avatar(opt.avatar_id)
                warm_up(opt.batch_size,avatar,160)
        except (RuntimeError, OSError, FileNotFoundError) as e:
            opt.no_model = True
            no_model_message = MODEL_LOAD_FAILED_MSG
            no_model_reason = "load_failed"
            model = None
            avatar = None
            logger.warning("Model load failed (wrong checkpoint or missing file). Server will start but digital human disabled. Use wav2lip256.pth from project Google Drive/Quark, not standard Wav2Lip. Error: %s", e)
    if opt.no_model:
        logger.warning("Starting in NO-MODEL mode (avatar disabled). Use ./run_local.sh and open the URL printed in the terminal.")

    # if opt.transport=='rtmp':
    #     thread_quit = Event()
    #     nerfreals[0] = build_nerfreal(0)
    #     rendthrd = Thread(target=nerfreals[0].render,args=(thread_quit,))
    #     rendthrd.start()
    if opt.transport=='virtualcam' and not getattr(opt, 'no_model', False) and model is not None:
        thread_quit = Event()
        nerfreals[0] = build_nerfreal(0)
        rendthrd = Thread(target=nerfreals[0].render,args=(thread_quit,))
        rendthrd.start()

    #############################################################################
    appasync = web.Application(client_max_size=1024**2*100)
    appasync.on_shutdown.append(on_shutdown)
    appasync.router.add_post("/offer", offer)
    appasync.router.add_post("/human", human)
    appasync.router.add_post("/humanaudio", humanaudio)
    appasync.router.add_post("/set_audiotype", set_audiotype)
    appasync.router.add_post("/record", record)
    appasync.router.add_post("/interrupt_talk", interrupt_talk)
    appasync.router.add_post("/is_speaking", is_speaking)
    appasync.router.add_get("/status", status)
    # Redirect root to webrtc UI so "http://localhost:8010" doesn't 403 (static / has no index)
    async def root_redirect(_request):
        raise web.HTTPFound("/webrtcapi.html")
    appasync.router.add_get("/", root_redirect)
    appasync.router.add_static('/', path='web')

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(appasync, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
    # Configure CORS on all routes.
    for route in list(appasync.router.routes()):
        cors.add(route)

    pagename='webrtcapi.html'
    if opt.transport=='rtmp':
        pagename='echoapi.html'
    elif opt.transport=='rtcpush':
        pagename='rtcpushapi.html'
    logger.info('start http server; http://<serverip>:'+str(opt.listenport)+'/'+pagename)
    logger.info('如果使用webrtc，推荐访问webrtc集成前端: http://<serverip>:'+str(opt.listenport)+'/dashboard.html')
    def run_server(runner):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner.setup())
        ports_to_try = [opt.listenport, 8011, 8012, 8888]
        for try_port in ports_to_try:
            if try_port != opt.listenport:
                logger.info('Port %s in use, trying %s...', opt.listenport, try_port)
            opt.listenport = try_port
            site = web.TCPSite(runner, '0.0.0.0', opt.listenport)
            try:
                loop.run_until_complete(site.start())
                break
            except OSError as e:
                if e.errno != 98 and e.errno != 48:  # Address already in use
                    raise
                if try_port == ports_to_try[-1]:
                    raise SystemExit('No port available (tried %s). Stop other apps using these ports.' % ports_to_try)
        logger.info('Serving at http://<serverip>:%s/%s', opt.listenport, pagename)
        if opt.transport=='rtcpush' and not getattr(opt, 'no_model', False):
            for k in range(opt.max_session):
                push_url = opt.push_url
                if k!=0:
                    push_url = opt.push_url+str(k)
                loop.run_until_complete(run(push_url,k))
        loop.run_forever()    
    #Thread(target=run_server, args=(web.AppRunner(appasync),)).start()
    run_server(web.AppRunner(appasync))

    #app.on_shutdown.append(on_shutdown)
    #app.router.add_post("/offer", offer)

    # print('start websocket server')
    # server = pywsgi.WSGIServer(('0.0.0.0', 8000), app, handler_class=WebSocketHandler)
    # server.serve_forever()
    
    
