import sys
import os
import re
import json
from argparse import ArgumentParser
from subprocess import call
import wget
import g2p_id
from simpleaudio import WaveObject
from platformdirs import user_cache_dir
from TTS.api import TTS
from .terbilang import terbilang

model_url = 'https://github.com/Wikidepia/indonesian-tts/releases/download/v1.2/checkpoint_1260000-inference.pth'
cache_dir = user_cache_dir('g2p_id')
os.makedirs(cache_dir, exist_ok=True)
model_file = os.path.join(cache_dir, 'checkpoint_1260000-inference.pth')

data_dir = os.path.join(g2p_id.__path__[0], 'data')
config_base_file = os.path.join(data_dir, 'config.json')
speakers_file = os.path.join(data_dir, 'speakers.pth')
config_file = 'config.json'

if not os.path.exists(config_file):
    with open(config_base_file) as f:
        s = f.read()
    d = json.loads(s)
    d['model_args']['speakers_file'] = speakers_file
    s = json.dumps(d)
    with open(config_file, 'w') as f:
        f.write(s)

_g2p_instance = None
_tts_instance = None

def get_g2p():
    global _g2p_instance
    if _g2p_instance is None:
        _g2p_instance = g2p_id.G2P()
    return _g2p_instance

def get_tts():
    global _tts_instance
    if _tts_instance is None:
        download_model_if_not_exists()
        _tts_instance = TTS()
        _tts_instance.load_tts_model_by_path(
            model_path=model_file,
            config_path=config_file
        )
    return _tts_instance

def download_model_if_not_exists():
    if not os.path.exists(model_file):
        print('Download', model_url)
        wget.download(model_url, out=cache_dir)
        print()
        print('Save', model_file)


def ganti_angka(s):
    while True:
        match = re.search(r'\d+', s)
        if not match:
            return s
        angka = int(match.group(0))
        t = terbilang(angka)
        awal, akhir = match.span()
        s = s[:awal] + t + s[akhir:]


def ganti_persen(s):
    while True:
        i = s.find('%')
        if i < 0:
            return s
        s = s[:i] + ' persen' + s[i+1:]


def ganti_titik_dua(s):
    while True:
        match = re.search(r'\b\w+:', s)
        if not match:
            return s
        awal, akhir = match.span()
        s = s[:akhir-1] + ',' + s[akhir:]


def text_normalization(content):
    text_list = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[-1] not in ['.', '?', '!']:
            line = line + '.'
        line = ganti_angka(line)
        line = ganti_persen(line)
        line = ganti_titik_dua(line)
        text_list.append(line)
    return '\n'.join(text_list)


def tts(content: str, speaker='ardi', output_file='tts_drat.wav') -> int:
    try:
        text = text_normalization(content)
        text_to_tts = get_g2p()(text)
        engine = get_tts()
        engine.tts_to_file(
            text=text_to_tts,
            speaker=speaker,
            file_path=output_file
        )
        return 0
    except Exception as e:
        print(f"Error during TTS: {e}")
        return 1


def main(argv=sys.argv[1:]):
    help_text = 'bisa file'
    speaker = 'ardi'
    help_speaker = f'default {speaker}, '\
                   'lainnya wibowo, gadis, JV-00264, SU-00060'
    output_file = 'tts_drat.wav'
    help_file = f'default {output_file}'
    pars = ArgumentParser()
    pars.add_argument('--text', required=True)
    pars.add_argument('--speaker', default=speaker, help=help_speaker)
    pars.add_argument('--output-file', default=output_file, help=help_file)
    option = pars.parse_args(sys.argv[1:])
    if os.path.exists(option.text):
        with open(option.text) as f:
            text = f.read()
    else:
        text = option.text
    if tts(text, option.speaker, option.output_file) != 0:
        return
    obj = WaveObject.from_wave_file(option.output_file)
    p = obj.play()
    p.wait_done()
