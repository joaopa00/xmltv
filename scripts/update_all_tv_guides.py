#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import pytz
import xmltv
import subprocess
from datetime import datetime, timedelta

SCRIPTS_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/'
ROOT_DIRECTORY = SCRIPTS_DIRECTORY + '../'
RAW_DIRECTORY = ROOT_DIRECTORY + 'raw/'

# The date format used in XMLTV (the %Z will go away in 0.6)
DATE_FORMAT = '%Y%m%d%H%M%S %Z'
DATE_FORMAT_NOTZ = '%Y%m%d%H%M%S'
TODAY = datetime.now()

COUNTRIES = {
    'fr': {
        'raw_min_size': 600000,
        'raw': 'tv_guide_fr_telerama{}.xml',
        'dst': 'tv_guide_fr{}.xml',
        'tz': 'Europe/Paris',
        'grabber_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama_fr_config.txt',
            '--no_htmltags',
            '--casting',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6, 7]
    },
    'be': {
        'raw_min_size': 150000,
        'raw': 'tv_guide_be_telerama{}.xml',
        'dst': 'tv_guide_be{}.xml',
        'tz': 'Europe/Paris',
        'grabber_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama_be_config.txt',
            '--no_htmltags',
            '--casting',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6, 7]
    },
    'uk': {
        'raw_min_size': 150000,
        'raw': 'tv_guide_uk_tvguide{}.xml',
        'dst': 'tv_guide_uk{}.xml',
        'tz': 'Europe/London',
        'grabber_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_uk_tvguide/tv_grab_uk_tvguide',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_uk_tvguide/tv_grab_uk_tvguide.conf',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6, 7]
    },
    'it': {
        'raw_min_size': 150000,
        'raw': 'tv_guide_it{}.xml',
        'dst': 'tv_guide_it{}.xml',
        'tz': 'Europe/Rome',
        'grabber_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_it/tv_grab_it',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_it/tv_grab_it.conf',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6]
    }
}


def remove_root_xmltv_files():
    """In root directory, remove all XMLTV files"""
    print('\n# Remove all XMLTV files in root directory', flush=True)
    for f in glob.glob(ROOT_DIRECTORY + '*.xml'):
        os.remove(f)


def remove_old_raw_files():
    """In 'raw' directory, remove old XMLTV and log files"""
    print('\n# Remove old XMLTV and log files of raw directory', flush=True)
    subexpr_to_remove = []
    for delta in range(3, 20):
        subexpr_to_remove.append((TODAY - timedelta(days=delta)).strftime("%Y%m%d"))
    for f in glob.glob(RAW_DIRECTORY + '*'):
        for expr in subexpr_to_remove:
            if expr in f:
                print('\t* Remove file ' + f, flush=True)
                os.remove(f)


def update_raw_files():
    """Update raw XMLTV files from grabbers"""
    print('\n# Update raw XMLTV files from grabbers', flush=True)
    my_env = os.environ.copy()
    my_env['HOME'] = SCRIPTS_DIRECTORY
    for delta in range(0, 8):
        day_to_grab = TODAY + timedelta(days=delta)
        print('\t* Grab TV guides of day {}'.format(day_to_grab.strftime("%d/%m/%Y")), flush=True)
        for country_code, country_infos in COUNTRIES.items():
            if delta not in country_infos['allowed_offsets']:
                continue
            xmltv_fp = RAW_DIRECTORY + country_infos['raw'].format('_' + day_to_grab.strftime("%Y%m%d"))
            print('\t\t- Grab TV guides of {} country in {}'.format(country_code, xmltv_fp), flush=True)
            run_cmd = True
            if delta == 1:  # If delta is 1, force grabber to run (fix issue #7)
                print('\t\t\t* Force file update (delta is 1) --> run grabber', flush=True)
            elif os.path.exists(xmltv_fp):
                xmltv_file_size = os.path.getsize(xmltv_fp)
                if xmltv_file_size < country_infos['raw_min_size']:
                    print('\t\t\t* This file already exists but its size is small 0_o ({} bytes) --> run grabber again'.format(xmltv_file_size), flush=True)
                else:
                    print('\t\t\t* This file already exists (size: {} bytes) --> Nothing to do'.format(xmltv_file_size), flush=True)
                    run_cmd = False
            if run_cmd:
                stdout_f = open(xmltv_fp + '_stdout.log', 'w')
                stderr_f = open(xmltv_fp + '_stderr.log', 'w')
                cmd = country_infos['grabber_cmd']
                cmd[-1] = xmltv_fp
                cmd[-3] = str(delta)
                print('\t\t\t* Run cmd:', ' '.join(cmd), flush=True)
                subprocess.run(cmd, env=my_env, stdout=stdout_f, stderr=stderr_f)
                stdout_f.close()
                stderr_f.close()
                print('\t\t\t* Final file size: {} bytes'.format(os.path.getsize(xmltv_fp)), flush=True)


def generate_new_xmltv_files():
    """In root directory, generate all new XMLTV files"""
    print('\n# Generate new XMLTV files in root directory', flush=True)
    for country_code, country_infos in COUNTRIES.items():
        print('\n* Processing of {} country:'.format(country_code), flush=True)

        # Retireve programmes from all raw xmltv files
        print('\t- Retireve TV shows from all xmltv files of this country', flush=True)
        country_infos['channels_l'] = []
        country_infos['programmes_local_datetime_l'] = []
        country_infos['programmes_l'] = []
        country_infos['data_d'] = {}

        for offset in range(-10, 20):
            date = TODAY + timedelta(days=offset)
            xmltv_fp = RAW_DIRECTORY + country_infos['raw'].format('_' + date.strftime("%Y%m%d"))
            if not os.path.exists(xmltv_fp):
                continue
            print('\t\t* Add TV shows from file {}'.format(xmltv_fp), flush=True)

            try:
                # Channels and data are the same for all days
                if not country_infos['data_d']:
                    country_infos['data_d'] = xmltv.read_data(open(xmltv_fp, 'r'))
                if not country_infos['channels_l']:
                    country_infos['channels_l'] = xmltv.read_channels(open(xmltv_fp, 'r'))

                # But for the programmes, we need to append each day
                programmes = xmltv.read_programmes(open(xmltv_fp, 'r'))

                # If there is no programme, delete this raw xmltv file
                if not programmes:
                    print('\t\t\t- This file does not contain any TV shows :-/, delete it', flush=True)
                    os.remove(xmltv_fp)
                else:
                    print('\t\t\t- This file contains {} TV shows'.format(len(programmes)), flush=True)
                    country_infos['programmes_local_datetime_l'].extend(list(programmes))
                    country_infos['programmes_l'].extend(list(programmes))

            except Exception:
                print('\t\t\t- This file seems to be corrupt :-/, delete it', flush=True)
                os.remove(xmltv_fp)

        # If data_d is still empty here, we can continue to the next country
        if not country_infos['data_d']:
            print('\t- None XMLTV file seems ok for this coutnry :-/', flush=True)
            continue

        print('\t- This country have a total of {} TV shows'.format(len(country_infos['programmes_local_datetime_l'])), flush=True)

        # Replace local datetime by UTC datetime for programmes entries
        for programme in country_infos['programmes_l']:
            for elt in ['start', 'stop']:
                s = programme[elt]

                # Remove timezone part to get %Y%m%d%H%M%S format
                s = s.split(' ')[0]

                # Get the naive datetime object
                d = datetime.strptime(s, DATE_FORMAT_NOTZ)

                # Add correct timezone
                tz = pytz.timezone(country_infos['tz'])
                d = tz.localize(d)

                # Convert to UTC timezone
                utc_tz = pytz.UTC
                d = d.astimezone(utc_tz)

                # Finally replace the datetime with the UTC one
                s = d.strftime(DATE_FORMAT_NOTZ)
                # print('Replace {} by {}'.format(programme[elt], s))
                programme[elt] = s

        # Write full xmltv files
        for fp_prefix in ['', '_local']:
            dst_fp = ROOT_DIRECTORY + country_infos['dst'].format(fp_prefix)
            print('\t- Write full xmltv file in {}'.format(os.path.basename(dst_fp)), flush=True)
            w = xmltv.Writer(
                source_info_url=country_infos['data_d']['source-info-url']
            )

            # Add channels
            for c in country_infos['channels_l']:
                w.addChannel(c)

            # Add programmes
            if fp_prefix == '_local':
                programmes_l = country_infos['programmes_local_datetime_l']
            else:
                programmes_l = country_infos['programmes_l']

            if not programmes_l:
                print('\t\t* This file does not contain any TV shows :-/, do not write it', flush=True)
                continue

            for p in programmes_l:
                w.addProgramme(p)

            # Write XMLTV file
            with open(dst_fp, 'wb') as f:
                w.write(f, pretty_print=True)

        # Write one day xmltv files
        print('\t- Write one day xmltv files:', flush=True)
        for fp_prefix in ['', '_local']:
            for offset in range(-2, 8):
                date = TODAY + timedelta(days=offset)
                date_s = date.strftime("%Y%m%d")
                dst_fp = ROOT_DIRECTORY + country_infos['dst'].format(fp_prefix + '_' + date_s)
                print('\t\t* Write day {} in {}'.format(date_s, os.path.basename(dst_fp)), flush=True)
                w = xmltv.Writer(
                    source_info_url=country_infos['data_d']['source-info-url']
                )

                # Add channels
                for c in country_infos['channels_l']:
                    w.addChannel(c)

                # Add programmes
                if fp_prefix == '_local':
                    programmes_l = country_infos['programmes_local_datetime_l']
                else:
                    programmes_l = country_infos['programmes_l']

                if not programmes_l:
                    print('\t\t\t- This file does not contain any TV shows :-/, do not write it', flush=True)
                    continue

                cnt = 0
                for p in programmes_l:
                    start_s = p['start'][0:8]
                    stop_s = p['stop'][0:8]
                    if start_s == date_s or stop_s == date_s:
                        w.addProgramme(p)
                        cnt = cnt + 1
                with open(dst_fp, 'wb') as f:
                    w.write(f, pretty_print=True)
                print('\t\t\t- Final file contains {} TV shows'.format(cnt), flush=True)

    print('\n* Merge all country tv guides in tv_guide_all.xml', flush=True)

    w = xmltv.Writer()

    for country_code, country_infos in COUNTRIES.items():
        if 'channels_l' in country_infos:
            for c in country_infos['channels_l']:
                w.addChannel(c)

    cnt = 0
    for country_code, country_infos in COUNTRIES.items():
        if 'programmes_l' in country_infos:
            for p in country_infos['programmes_l']:
                w.addProgramme(p)
                cnt = cnt + 1

    with open(ROOT_DIRECTORY + 'tv_guide_all.xml', 'wb') as f:
        w.write(f, pretty_print=True)
    print('\t\t- Final file contains {} TV shows'.format(cnt), flush=True)

    print('\n* Merge all country tv guides in tv_guide_all_local.xml', flush=True)

    w = xmltv.Writer()

    for country_code, country_infos in COUNTRIES.items():
        if 'channels_l' in country_infos:
            for c in country_infos['channels_l']:
                w.addChannel(c)

    cnt = 0
    for country_code, country_infos in COUNTRIES.items():
        if 'programmes_local_datetime_l' in country_infos:
            for p in country_infos['programmes_local_datetime_l']:
                w.addProgramme(p)
                cnt = cnt + 1

    with open(ROOT_DIRECTORY + 'tv_guide_all_local.xml', 'wb') as f:
        w.write(f, pretty_print=True)
    print('\t\t- Final file contains {} TV shows'.format(cnt), flush=True)


def main():
    print('\n# Start script at', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), flush=True)
    remove_root_xmltv_files()
    remove_old_raw_files()
    update_raw_files()
    generate_new_xmltv_files()
    print('\n# Exit script at', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), flush=True)


if __name__ == '__main__':
    main()


"""
    'fr_tnt': {
        'raw_min_size': 600000,
        'raw': 'tv_guide_fr_telerama{}.xml',
        'dst': 'tv_guide_fr_tnt{}.xml',
        'tz': 'Europe/Paris',
        'channels_to_add': [
            'C192.api.telerama.fr',  # TF1
            'C4.api.telerama.fr',  # France 2
            'C80.api.telerama.fr',  # France 3
            'C34.api.telerama.fr',  # Canal+
            'C47.api.telerama.fr',  # France 5
            'C118.api.telerama.fr',  # M6
            'C111.api.telerama.fr',  # Arte
            'C445.api.telerama.fr',  # C8
            'C119.api.telerama.fr',  # W9
            'C195.api.telerama.fr',  # TMC
            'C446.api.telerama.fr',  # TFX
            'C444.api.telerama.fr',  # NRJ 12
            'C234.api.telerama.fr',  # LCP
            'C78.api.telerama.fr',  # France 4
            'C481.api.telerama.fr',  # BFM TV
            'C226.api.telerama.fr',  # CNEWS
            'C458.api.telerama.fr',  # CSTAR
            'C482.api.telerama.fr',  # Gulli
            'C160.api.telerama.fr',  # France O
            'C1404.api.telerama.fr',  # TF1 Séries Films
            'C1401.api.telerama.fr',  # L'équipe
            'C1403.api.telerama.fr',  # 6ter
            'C1402.api.telerama.fr',  # RMC Story
            'C1400.api.telerama.fr',  # RMC Découverte
            'C1399.api.telerama.fr',  # Chérie 25
            'C112.api.telerama.fr',  # LCI
            'C2111.api.telerama.fr'  # Franceinfo
        ],
        'grabber_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama_fr_config.txt',
            '--no_htmltags',
            '--casting',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ]
"""
