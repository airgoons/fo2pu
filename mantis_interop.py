from enum import StrEnum
from collections import Counter

import dcs

class FactionTag_MantisTagLUT:
    # faction_tag: mantis_tag
    _data = {
        "BLUE": "NATO SAM",
        "RED": "RuAF SAM"
    }

    @staticmethod
    def get_mantis_tag(faction_tag):
        return FactionTag_MantisTagLUT._data.get(faction_tag, None)


class MantisSamTag_DcsObjLUT:
    # mantis_tag: dcs_obj
    _data = {
        "Hawk": [dcs.vehicles.AirDefence.Hawk_cwar, dcs.vehicles.AirDefence.Hawk_ln, dcs.vehicles.AirDefence.Hawk_pcp, dcs.vehicles.AirDefence.Hawk_sr, dcs.vehicles.AirDefence.Hawk_tr],
        "NASAMS": [dcs.vehicles.AirDefence.NASAMS_Command_Post, dcs.vehicles.AirDefence.NASAMS_LN_B, dcs.vehicles.AirDefence.NASAMS_LN_C, dcs.vehicles.AirDefence.NASAMS_Radar_MPQ64F1],
        "Patriot": [dcs.vehicles.AirDefence.Patriot_AMG, dcs.vehicles.AirDefence.Patriot_cp, dcs.vehicles.AirDefence.Patriot_ECS, dcs.vehicles.AirDefence.Patriot_EPP, dcs.vehicles.AirDefence.Patriot_ln, dcs.vehicles.AirDefence.Patriot_str],
        "Rapier": [dcs.vehicles.AirDefence.rapier_fsa_blindfire_radar, dcs.vehicles.AirDefence.rapier_fsa_launcher, dcs.vehicles.AirDefence.rapier_fsa_optical_tracker_unit],
        "SA-2": [dcs.vehicles.AirDefence.p_19_s_125_sr, dcs.vehicles.AirDefence.RD_75, dcs.vehicles.AirDefence.S_75M_Volhov, dcs.vehicles.AirDefence.SNR_75V],
        "SA-3": [dcs.vehicles.AirDefence.p_19_s_125_sr, dcs.vehicles.AirDefence.snr_s_125_tr, dcs.vehicles.AirDefence.x_5p73_s_125_ln],
        "SA-5": [dcs.vehicles.AirDefence.p_19_s_125_sr, dcs.vehicles.AirDefence.P14_SR, dcs.vehicles.AirDefence.RLS_19J6, dcs.vehicles.AirDefence.RPC_5N62V, dcs.vehicles.AirDefence.S_200_Launcher],
        "SA-6": [dcs.vehicles.AirDefence.Kub_1S91_str, dcs.vehicles.AirDefence.Kub_2P25_ln],
        "SA-10": [dcs.vehicles.AirDefence.S_300PS_5P85C_ln, dcs.vehicles.AirDefence.S_300PS_5P85D_ln, dcs.vehicles.AirDefence.S_300PS_54K6_cp, dcs.vehicles.AirDefence.S_300PS_40B6M_tr, dcs.vehicles.AirDefence.S_300PS_64H6E_sr, dcs.vehicles.AirDefence.S_300PS_40B6MD_sr_19J6, dcs.vehicles.AirDefence.S_300PS_5H63C_30H6_tr, dcs.vehicles.AirDefence.S_300PS_40B6MD_sr],
        "SA-11": [dcs.vehicles.AirDefence.SA_11_Buk_CC_9S470M1, dcs.vehicles.AirDefence.SA_11_Buk_LN_9A310M1, dcs.vehicles.AirDefence.SA_11_Buk_SR_9S18M1],
        "Roland": [dcs.vehicles.AirDefence.Roland_ADS, dcs.vehicles.AirDefence.Roland_Radar],
        "Gepard": [dcs.vehicles.AirDefence.Gepard],
        "HQ-7": [dcs.vehicles.AirDefence.HQ_7_LN_P, dcs.vehicles.AirDefence.HQ_7_LN_SP, dcs.vehicles.AirDefence.HQ_7_STR_SP],
        "SA-9": [dcs.vehicles.AirDefence.Strela_1_9P31],
        "SA-8": [dcs.vehicles.AirDefence.Osa_9A33_ln],
        "SA-19": [dcs.vehicles.AirDefence.x_2S6_Tunguska],
        "SA-15": [dcs.vehicles.AirDefence.Tor_9A331],
        "SA-13": [dcs.vehicles.AirDefence.Strela_10M3],
        "Avenger": [dcs.vehicles.AirDefence.M1097_Avenger],
        "Chaparral": [dcs.vehicles.AirDefence.M48_Chaparral],
        "Linebacker": [dcs.vehicles.AirDefence.M6_Linebacker],
        "Silkworm": [dcs.vehicles.MissilesSS.hy_launcher, dcs.vehicles.MissilesSS.Silkworm_SR],
        "C-RAM": [dcs.vehicles.AirDefence.HEMTT_C_RAM_Phalanx],
        "SA-10B": [],
        "SA-17": [],
        "SA-20A": [],
        "SA-20B": [],
        "S-300VM": [],
        "S-300V4": [],
        "S-400": [],
        "HQ-2": [],
        "TAMIR IDFA": [],
        "STUNNER IDFA": [],
        "Nike": [],
        "Dog Ear": [dcs.vehicles.AirDefence.Dog_Ear_radar],
        "Pantsir S1": [dcs.vehicles.AirDefence.CHAP_PantsirS1],
        "Tor M2": [dcs.vehicles.AirDefence.CHAP_TorM2],
        "IRIS-T SLM": [dcs.vehicles.AirDefence.CHAP_IRISTSLM_CP, dcs.vehicles.AirDefence.CHAP_IRISTSLM_LN, dcs.vehicles.AirDefence.CHAP_IRISTSLM_STR],
        "SON-9": [dcs.vehicles.AirDefence.SON_9]
    }
    
    @staticmethod
    def get_dcs_unit_set(mantis_tag):
        return MantisSamTag_DcsObjLUT._data.get(mantis_tag, None)

    @staticmethod
    def get_best_mantis_tag(dcs_unit_set):
        counts = {}
        for tag, unit_set in MantisSamTag_DcsObjLUT._data.items():
            count = sum(item in set(unit_set) for item in dcs_unit_set)
            counts[tag] = count
        
        mantis_tag = max(counts, key=lambda k: counts[k])

        if counts[mantis_tag] == 0:
            return None
        else:
            return mantis_tag
