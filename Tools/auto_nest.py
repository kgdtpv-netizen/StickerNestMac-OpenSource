#!/usr/bin/env python3
# 独立异形套料器：读 PNG 文件夹 -> 输出布局 JSON(每张的中心mm/缩放/角度)+ 预览PNG
# 用法: auto_nest.py <png_folder> <out_json> [gapMM] [paperW] [paperH] [dpi] [seconds] [minScale] [maxScale] [targetLongSideMM]
import sys, os, glob, json, time, random, math, itertools, re
import numpy as np, cv2
from numpy.fft import rfft2, irfft2

folder   = sys.argv[1]
out_json = sys.argv[2]
GAP   = float(sys.argv[3]) if len(sys.argv)>3 else 6.0
PW    = float(sys.argv[4]) if len(sys.argv)>4 else 419.95
PH    = float(sys.argv[5]) if len(sys.argv)>5 else 594.02
DPI   = float(sys.argv[6]) if len(sys.argv)>6 else 300.0
SECS  = float(sys.argv[7]) if len(sys.argv)>7 else 90.0
SMIN  = float(sys.argv[8]) if len(sys.argv)>8 else 0.85
SMAX  = float(sys.argv[9]) if len(sys.argv)>9 else 1.25
BASE_MM = float(sys.argv[10]) if len(sys.argv)>10 else 108.0
SEED = int(os.environ.get("STICKERNEST_AUTO_NEST_SEED", "0"))
POLISH_BASE_JSON=os.environ.get("STICKERNEST_POLISH_BASE_JSON","").strip()
LOW_ALPHA_READABLE_POSTPROCESS=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_POSTPROCESS","0")!="0"
LOW_ALPHA_READABLE_SCALE_TRANSFER=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_SCALE_TRANSFER","0")!="0"
LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW","0")!="0"
LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK","0")!="0"
LOW_ALPHA_READABLE_BAND_VOID_FILL=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL","0")!="0"
LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR","0")!="0"
LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE","0")!="0"
LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE","0")!="0"
LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL=os.environ.get("STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL","0")!="0"
DOWN  = 20  # 工作网格降采样
RECOVERY_24P1=os.environ.get("STICKERNEST_RECOVERY_24P1","1")!="0"
RECOVERY_MIN_TARGET=float(os.environ.get("STICKERNEST_RECOVERY_24P1_TARGET_MIN_MM","115.0"))
RECOVERY_MAX_BLOCKERS=max(1,int(os.environ.get("STICKERNEST_RECOVERY_24P1_MAX_BLOCKERS","5")))
RECOVERY_TRACE_ROUNDS=max(1,int(os.environ.get("STICKERNEST_RECOVERY_24P1_TRACE_ROUNDS","3")))
RECOVERY_DEBUG=os.environ.get("STICKERNEST_RECOVERY_DEBUG","0")=="1"
RECOVERY_MULTI=os.environ.get("STICKERNEST_RECOVERY_MULTI","0")!="0"
RECOVERY_MULTI_MIN_TARGET=float(os.environ.get("STICKERNEST_RECOVERY_MULTI_TARGET_MIN_MM","117.0"))
RECOVERY_MULTI_MAX_PENDING=max(2,int(os.environ.get("STICKERNEST_RECOVERY_MULTI_MAX_PENDING","2")))
RECOVERY_MULTI_MAX_BLOCKERS=max(1,int(os.environ.get("STICKERNEST_RECOVERY_MULTI_MAX_BLOCKERS","3")))
RECOVERY_MULTI_MAX_COMBOS=max(1,int(os.environ.get("STICKERNEST_RECOVERY_MULTI_MAX_COMBOS","16")))
RECOVERY_MULTI_MAX_VARIANTS=max(4,int(os.environ.get("STICKERNEST_RECOVERY_MULTI_MAX_VARIANTS","18")))
HUMAN_IMITATION=os.environ.get("STICKERNEST_HUMAN_IMITATION","0")!="0"
MANUAL_STAGGER=os.environ.get("STICKERNEST_MANUAL_STAGGER","0")!="0"
MANUAL_STAGGER_ROTATE=os.environ.get("STICKERNEST_MANUAL_STAGGER_ROTATE","1")!="0"
MANUAL_STAGGER_SAFE_ROTATE=os.environ.get("STICKERNEST_MANUAL_STAGGER_SAFE_ROTATE","0")!="0"
MANUAL_STAGGER_STRENGTH=float(os.environ.get("STICKERNEST_MANUAL_STAGGER_STRENGTH","0.85"))
ROW_PHASE_BASE_PROBE=os.environ.get("STICKERNEST_ROW_PHASE_BASE_PROBE","0")!="0"
STAGGER_SLOT_BEAM_SEED=os.environ.get("STICKERNEST_STAGGER_SLOT_BEAM_SEED","0")!="0"
STAGGER_SLOT_BEAM_SEED_WIDTH=max(1,min(6,int(os.environ.get("STICKERNEST_STAGGER_SLOT_BEAM_SEED_WIDTH","3"))))
STAGGER_SLOT_BEAM_SEED_NODE_LIMIT=max(100,min(3000,int(os.environ.get("STICKERNEST_STAGGER_SLOT_BEAM_SEED_NODE_LIMIT","1200"))))
STAGGER_SLOT_BEAM_SEED_CANDIDATES=max(3,min(10,int(os.environ.get("STICKERNEST_STAGGER_SLOT_BEAM_SEED_CANDIDATES","7"))))
VOID_RELOCATE=os.environ.get("STICKERNEST_VOID_RELOCATE","0")!="0"
MANUAL_ROW_REBALANCE=os.environ.get("STICKERNEST_MANUAL_ROW_REBALANCE","1")!="0"
MICRO_REFIT=os.environ.get("STICKERNEST_MICRO_REFIT","1")!="0"
LOCAL_CLUSTER_REPACK=os.environ.get("STICKERNEST_LOCAL_CLUSTER_REPACK","1")!="0"
LOCAL_CLUSTER_REPACK_TARGETS=max(1,int(os.environ.get("STICKERNEST_LOCAL_CLUSTER_REPACK_TARGETS","12")))
LOCAL_CLUSTER_REPACK_NEAR=max(4,int(os.environ.get("STICKERNEST_LOCAL_CLUSTER_REPACK_NEAR","7")))
LOCAL_CLUSTER_REPACK_POSITIONS=max(12,int(os.environ.get("STICKERNEST_LOCAL_CLUSTER_REPACK_POSITIONS","52")))
LOCAL_CLUSTER_REPACK_NODE_LIMIT=max(1000,int(os.environ.get("STICKERNEST_LOCAL_CLUSTER_REPACK_NODE_LIMIT","14000")))
MATERIAL_ALPHA_TOPUP=os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP","0")!="0"
MATERIAL_ALPHA_TOPUP_TARGET=float(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_TARGET","0.550"))
MATERIAL_ALPHA_TOPUP_MIN_GAIN=float(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MIN_GAIN","0.0015"))
MATERIAL_ALPHA_TOPUP_MIN_ACCEPT=float(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MIN_ACCEPT","0.550"))
MATERIAL_ALPHA_TOPUP_MAX_DEFICIT=float(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MAX_DEFICIT","0.008"))
MATERIAL_ALPHA_TOPUP_MAX_MOVES=max(1,int(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MAX_MOVES","8")))
MATERIAL_ALPHA_TOPUP_MAX_NUDGE=max(0,int(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MAX_NUDGE","2")))
MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE=int(os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE","60"))
MATERIAL_ALPHA_TOPUP_SEEDS=os.environ.get("STICKERNEST_MATERIAL_ALPHA_TOPUP_SEEDS","4")
MATERIAL_ALPHA_TOPUP_APPLIED=False
MATERIAL_ALPHA_TOPUP_PARTIAL=False
MATERIAL_ALPHA_TOPUP_MOVES=0
MULTI_PIECE_TOPUP=os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP","0")!="0"
MULTI_PIECE_TOPUP_TARGET=float(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_TARGET",str(MATERIAL_ALPHA_TOPUP_TARGET)))
MULTI_PIECE_TOPUP_MIN_GAIN=float(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_MIN_GAIN","0.0003"))
MULTI_PIECE_TOPUP_MIN_ACCEPT=float(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_MIN_ACCEPT",str(MATERIAL_ALPHA_TOPUP_MIN_ACCEPT)))
MULTI_PIECE_TOPUP_MAX_MOVES=max(1,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_MAX_MOVES","3")))
MULTI_PIECE_TOPUP_MAX_BLOCKERS=max(1,min(3,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_MAX_BLOCKERS","2"))))
MULTI_PIECE_TOPUP_MAX_NUDGE=max(0,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_MAX_NUDGE","8")))
MULTI_PIECE_TOPUP_RELOCATE_RADIUS=max(8,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_RELOCATE_RADIUS","34")))
MULTI_PIECE_TOPUP_OPTIONS=max(4,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_OPTIONS","8")))
MULTI_PIECE_TOPUP_TARGETS=max(3,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_TARGETS","8")))
MULTI_PIECE_TOPUP_NODE_LIMIT=max(200,int(os.environ.get("STICKERNEST_MULTI_PIECE_TOPUP_NODE_LIMIT","14000")))
MULTI_PIECE_TOPUP_APPLIED=False
MULTI_PIECE_TOPUP_MOVES=0
LOCAL_ADAPTER=os.environ.get("STICKERNEST_LOCAL_ADAPTER","0")!="0"
LOCAL_ADAPTER_V2=os.environ.get("STICKERNEST_LOCAL_ADAPTER_V2","0")!="0"
LOCAL_ADAPTER_MIN_ACCEPT=float(os.environ.get("STICKERNEST_LOCAL_ADAPTER_MIN_ACCEPT","0.5532"))
LOCAL_ADAPTER_MIN_GAIN=float(os.environ.get("STICKERNEST_LOCAL_ADAPTER_MIN_GAIN","0.0003"))
LOCAL_ADAPTER_NODE_LIMIT=max(200,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_NODE_LIMIT","8000")))
LOCAL_ADAPTER_NEAR=max(3,min(8,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_NEAR","7"))))
LOCAL_ADAPTER_OPTIONS=max(6,min(32,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_OPTIONS","18"))))
LOCAL_ADAPTER_TARGET_TILES=os.environ.get("STICKERNEST_LOCAL_ADAPTER_TARGET_TILES","5:4,4:4,8:4,3:6,2:3,8:7,9:5")
LOCAL_ADAPTER_TARGET_MODE=os.environ.get("STICKERNEST_LOCAL_ADAPTER_TARGET_MODE","fixed").strip().lower()
LOCAL_ADAPTER_MAX_CLUSTER_SIZE=max(3,min(4,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_MAX_CLUSTER_SIZE","4" if LOCAL_ADAPTER_V2 else "3"))))
LOCAL_ADAPTER_V2_MIN_ACCEPT=float(os.environ.get("STICKERNEST_LOCAL_ADAPTER_V2_MIN_ACCEPT","0.5536"))
LOCAL_ADAPTER_FINE_RADIUS=max(0,min(6,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_FINE_RADIUS","4"))))
LOCAL_ADAPTER_FINE_OFFSETS=tuple(range(-LOCAL_ADAPTER_FINE_RADIUS,LOCAL_ADAPTER_FINE_RADIUS+1))
LOCAL_ADAPTER_MAX_SIZE_CV_INCREASE=float(os.environ.get("STICKERNEST_LOCAL_ADAPTER_MAX_SIZE_CV_INCREASE","0.006"))
LOCAL_ADAPTER_SCALE_FACTORS=(1.0,1.003,1.006,1.009,1.012)
LOCAL_ADAPTER_V2_SCALE_FACTORS=(1.0,1.003,1.006,1.009,1.012,1.015,1.018)
LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT=max(3,min(12,int(os.environ.get("STICKERNEST_LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT","4"))))
LOCAL_ADAPTER_DEBUG=os.environ.get("STICKERNEST_LOCAL_ADAPTER_DEBUG","0")!="0"
LOCAL_ADAPTER_APPLIED=False
LOCAL_ADAPTER_V2_APPLIED=False
LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED=False
LOCAL_ADAPTER_MOVES=0
STRUCTURAL_MICRO_GROW=os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW","0")!="0"
STRUCTURAL_MICRO_GROW_MIN_ACCEPT=float(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_MIN_ACCEPT","0.5536"))
STRUCTURAL_MICRO_GROW_MIN_GAIN=float(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_MIN_GAIN","0.0002"))
STRUCTURAL_MICRO_GROW_MAX_BLOCKERS=max(0,min(3,int(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_MAX_BLOCKERS","1"))))
STRUCTURAL_MICRO_GROW_NODE_LIMIT=max(200,int(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_NODE_LIMIT","9000")))
STRUCTURAL_MICRO_GROW_OPTIONS=max(6,min(32,int(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_OPTIONS","24"))))
STRUCTURAL_MICRO_GROW_RADIUS=max(8,min(48,int(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_RADIUS","36"))))
STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS=max(1,min(8,int(os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS","4"))))
STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK=os.environ.get("STICKERNEST_STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK","0")!="0"
STRUCTURAL_MICRO_GROW_APPLIED=False
STRUCTURAL_MICRO_GROW_MOVES=0
SCALE_TRANSFER=os.environ.get("STICKERNEST_SCALE_TRANSFER","0")!="0"
SCALE_TRANSFER_MIN_ACCEPT=float(os.environ.get("STICKERNEST_SCALE_TRANSFER_MIN_ACCEPT","0.5545"))
SCALE_TRANSFER_MIN_GAIN=float(os.environ.get("STICKERNEST_SCALE_TRANSFER_MIN_GAIN","0.00025"))
SCALE_TRANSFER_NODE_LIMIT=max(500,min(3000000,int(os.environ.get("STICKERNEST_SCALE_TRANSFER_NODE_LIMIT","2600000"))))
SCALE_TRANSFER_NEAR=max(3,min(10,int(os.environ.get("STICKERNEST_SCALE_TRANSFER_NEAR","7"))))
SCALE_TRANSFER_APPLIED=False
SCALE_TRANSFER_MOVES=0
SMALL_GROUP_MATERIAL_REPACK=os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK","0")!="0"
SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT=float(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT","0.5542"))
SMALL_GROUP_MATERIAL_REPACK_MIN_GAIN=float(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MIN_GAIN","0.00008"))
SMALL_GROUP_MATERIAL_REPACK_TARGETS=max(2,min(10,int(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_TARGETS","5"))))
SMALL_GROUP_MATERIAL_REPACK_NEAR=max(4,min(8,int(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_NEAR","6"))))
SMALL_GROUP_MATERIAL_REPACK_OPTIONS=max(4,min(18,int(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_OPTIONS","10"))))
SMALL_GROUP_MATERIAL_REPACK_MAX_CLUSTER_SIZE=max(3,min(4,int(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MAX_CLUSTER_SIZE","3"))))
SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT=max(500,min(16000,int(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT","7000"))))
SMALL_GROUP_MATERIAL_REPACK_MAX_SIZE_CV_INCREASE=float(os.environ.get("STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MAX_SIZE_CV_INCREASE","0.007"))
SMALL_GROUP_MATERIAL_REPACK_APPLIED=False
SMALL_GROUP_MATERIAL_REPACK_MOVES=0
BAND_VOID_FILL_MIN_ACCEPT=float(os.environ.get("STICKERNEST_BAND_VOID_FILL_MIN_ACCEPT","0.4623"))
BAND_VOID_FILL_MIN_GAIN=float(os.environ.get("STICKERNEST_BAND_VOID_FILL_MIN_GAIN","0.00012"))
BAND_VOID_FILL_TARGETS=max(2,min(10,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_TARGETS","6"))))
BAND_VOID_FILL_DONORS=max(4,min(18,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_DONORS","10"))))
BAND_VOID_FILL_OPTIONS=max(4,min(24,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_OPTIONS","18"))))
BAND_VOID_FILL_NODE_LIMIT=max(500,min(60000,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_NODE_LIMIT","30000"))))
BAND_VOID_FILL_APPLIED=False
BAND_VOID_FILL_MOVES=0
BAND_VOID_FILL_PAIR_MIN_VOID_GAIN=float(os.environ.get("STICKERNEST_BAND_VOID_FILL_PAIR_MIN_VOID_GAIN","0.0025"))
BAND_VOID_FILL_PAIR_NODE_LIMIT=max(500,min(90000,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_PAIR_NODE_LIMIT","45000"))))
BAND_VOID_FILL_PAIR_BACKFILLS=max(2,min(12,int(os.environ.get("STICKERNEST_BAND_VOID_FILL_PAIR_BACKFILLS","6"))))
BAND_VOID_FILL_PAIR_APPLIED=False
BAND_VOID_FILL_PAIR_MOVES=0
RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN=float(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN","0.0015"))
RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT=max(500,min(90000,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT","45000"))))
RIGHT_CENTER_VOID_RELOCATE_TARGETS=max(2,min(12,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_TARGETS","8"))))
RIGHT_CENTER_VOID_RELOCATE_DONORS=max(4,min(18,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_DONORS","12"))))
RIGHT_CENTER_VOID_RELOCATE_OPTIONS=max(4,min(24,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_OPTIONS","18"))))
RIGHT_CENTER_VOID_RELOCATE_APPLIED=False
RIGHT_CENTER_VOID_RELOCATE_MOVES=0
RIGHT_CENTER_VOID_RELOCATE_GAIN=0.0
RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE=0.0
RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER=0.0
RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE=0.0
RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN=float(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN","0.0002"))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN=float(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN","0.0020"))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT=max(500,min(120000,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT","60000"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_TARGETS=max(2,min(12,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_TARGETS","8"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_DONORS=max(4,min(18,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_DONORS","12"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_OPTIONS=max(4,min(24,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_OPTIONS","14"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_BACKFILLS=max(2,min(12,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_BACKFILLS","6"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS=max(1,min(8,int(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILLS","4"))))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN=float(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN","0.0001"))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN=float(os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN","0.0005"))
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET=os.environ.get("STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_RESIDUAL_TARGET","0")!="0"
RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED=False
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED=False
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MOVES=0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES=0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED=False
RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_MOVES=0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_ALPHA_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_VOID_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED=False
RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES=0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN=0.0
RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_BEFORE=0.0
RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER=0.0
RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_BEFORE=0.0
RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER=0.0
Y_BIAS=float(os.environ.get("STICKERNEST_Y_BIAS","-0.35"))
HUMAN_ROWS=max(1,int(os.environ.get("STICKERNEST_HUMAN_ROWS","5")))
HUMAN_COLS=max(1,int(os.environ.get("STICKERNEST_HUMAN_COLS","5")))
READABILITY_GUARD=os.environ.get("STICKERNEST_READABILITY_GUARD","1")!="0"
MIN_READABLE_RATIO=float(os.environ.get("STICKERNEST_MIN_READABLE_RATIO","0.52"))
MIN_UPRIGHT_RATIO=float(os.environ.get("STICKERNEST_MIN_UPRIGHT_RATIO","0.28"))
MAX_UPSIDE_RATIO=float(os.environ.get("STICKERNEST_MAX_UPSIDE_RATIO","0.24"))
MAX_SIDEWAYS_RATIO=float(os.environ.get("STICKERNEST_MAX_SIDEWAYS_RATIO","0.12"))
MAX_HARD_OTHER_RATIO=float(os.environ.get("STICKERNEST_MAX_HARD_OTHER_RATIO","0.12"))
MAX_HARD_ROTATION_RATIO=float(os.environ.get("STICKERNEST_MAX_HARD_ROTATION_RATIO","0.44"))
HARD_REJECT_UPSIDE_RATIO=float(os.environ.get("STICKERNEST_HARD_REJECT_UPSIDE_RATIO","0.52"))
HARD_REJECT_SIDEWAYS_RATIO=float(os.environ.get("STICKERNEST_HARD_REJECT_SIDEWAYS_RATIO","0.28"))
HARD_REJECT_HARD_RATIO=float(os.environ.get("STICKERNEST_HARD_REJECT_HARD_RATIO","0.60"))
HARD_REJECT_MIN_READABLE_RATIO=float(os.environ.get("STICKERNEST_HARD_REJECT_MIN_READABLE_RATIO","0.32"))
UPSIDE_RESCUE_REFIT=os.environ.get("STICKERNEST_UPSIDE_RESCUE_REFIT","1")!="0"
UPSIDE_RESCUE_MAX_ALPHA_LOSS=float(os.environ.get("STICKERNEST_UPSIDE_RESCUE_MAX_ALPHA_LOSS","0.012"))
UPSIDE_RESCUE_MIN_ALPHA=float(os.environ.get("STICKERNEST_UPSIDE_RESCUE_MIN_ALPHA","0.525"))
def c(mm): return max(1,int(round(mm/25.4*DPI/DOWN)))
def cceil(mm): return max(0,int(math.ceil(mm/25.4*DPI/DOWN)))
def csigned(mm): return int(round(float(mm)/25.4*DPI/DOWN))
SW,SH = c(PW), c(PH); BASE=c(BASE_MM); G=max(1,c(GAP)//2)
# Actual pairwise gap realized after DOWN-grid quantization: each piece is dilated
# by G cells, so two contents end up 2*G*DOWN px apart. The nominal GAP mm is coarse
# (e.g. 6mm -> ~6.8mm, 5mm -> ~3.4mm); surfaced so the user knows the true cut width.
EFFECTIVE_GAP_MM = 2.0*G*DOWN*25.4/DPI
print(f"gap_precision nominal={GAP:.2f}mm effective={EFFECTIVE_GAP_MM:.2f}mm down={DOWN} G={G}", file=sys.stderr)
GAP_MODEL="swift_square"
EDGE_SAFETY_MM=float(os.environ.get("STICKERNEST_EDGE_SAFETY_MM","4.0"))
EDGE_TOTAL=max(0,cceil(EDGE_SAFETY_MM))
EDGE_BLOCK=max(0,EDGE_TOTAL-G)
AREASIDE=(SW*SH/len(__import__('glob').glob(__import__('os').path.join(folder,'*.png'))) )**0.5*0.62

def load_manual_policy():
    candidates=[
        os.path.join(os.path.dirname(__file__),"manual_layout_policy.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)),"Resources","manual_layout_policy.json"),
        os.path.join(os.getcwd(),"Resources","manual_layout_policy.json"),
    ]
    for path in candidates:
        try:
            with open(path,"r",encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

MANUAL_POLICY=load_manual_policy()

def load_stagger_policy():
    candidates=[
        os.path.join(os.path.dirname(__file__),"manual_stagger_policy.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)),"Resources","manual_stagger_policy.json"),
        os.path.join(os.getcwd(),"Resources","manual_stagger_policy.json"),
    ]
    for path in candidates:
        try:
            with open(path,"r",encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

STAGGER_POLICY=load_stagger_policy()

def reserved_occ():
    occ=np.zeros((SH,SW),bool)
    # Keep real sticker content about EDGE_SAFETY_MM away from all sheet edges.
    # The placed mask already includes half the pair gap on each side, so only
    # block the remaining edge strip to avoid wasting an extra 6mm near borders.
    if EDGE_BLOCK>0:
        occ[:EDGE_BLOCK,:]=True
        occ[max(0,SH-EDGE_BLOCK):,:]=True
        occ[:,:EDGE_BLOCK]=True
        occ[:,max(0,SW-EDGE_BLOCK):]=True
    # StickerNestMac A2 template: four registration marks + bottom QR.
    # These are the same protected regions used by the Swift renderer.
    if abs(PW-419.95)<2 and abs(PH-594.02)<2 and abs(DPI-300)<1:
        rects=[
            (106,106,224,224,45),
            (4630,106,224,224,45),
            (106,6686,224,224,45),
            (4630,6686,224,224,45),
            (2399,6806,169,168,130),
        ]
        for x,y,w,h,pad in rects:
            x0=max(0,int(math.floor((x-pad)/DOWN)))
            y0=max(0,int(math.floor((y-pad)/DOWN)))
            x1=min(SW,int(math.ceil((x+w+pad)/DOWN)))
            y1=min(SH,int(math.ceil((y+h+pad)/DOWN)))
            if x1>x0 and y1>y0:
                occ[y0:y1,x0:x1]=True
    return occ

BASE_OCC=reserved_occ()

def natural_key(path):
    name=os.path.basename(path)
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)",name)]

files = sorted(glob.glob(os.path.join(folder,"*.png")), key=natural_key)
raw=[]   # (name, mask cropped bool)
for f in files:
    im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    if im is None: continue
    if im.ndim==3 and im.shape[2]==4: a = im[:,:,3]>30
    else: a = np.ones(im.shape[:2],bool)
    ys,xs=np.where(a)
    if len(xs)==0: continue
    raw.append((os.path.basename(f), a[ys.min():ys.max()+1, xs.min():xs.max()+1]))
N=len(raw)
ANG=[0,8,352,12,348,15,345]
SAFE_MANUAL_STAGGER_ANGLES=[30,330]
if MANUAL_STAGGER and MANUAL_STAGGER_ROTATE:
    if MANUAL_STAGGER_SAFE_ROTATE:
        manual_stagger_extra_angles=SAFE_MANUAL_STAGGER_ANGLES
    else:
        manual_stagger_extra_angles=[30,330,90,270,180,75,285,105,255]
    for _a in manual_stagger_extra_angles:
        if _a not in ANG:
            ANG.append(_a)

def unit_alpha_eq(mask):
    h,w=mask.shape
    f=BASE/max(h,w)
    m=cv2.resize(mask.astype(np.uint8)*255,(max(1,int(w*f)),max(1,int(h*f))),interpolation=cv2.INTER_AREA)
    return max(1.0, math.sqrt(float((m>120).sum())))

# Manual A2 sheets show users balance by visual/person size, not by the raw crop
# longest side. Thin or low-fill cutouts need a larger base scale; dense blocky
# cutouts need a smaller one. This keeps final sizes closer to the human samples.
VISUAL_POWER=float(os.environ.get("STICKERNEST_VISUAL_BALANCE_POWER","0.15"))
VISUAL_MIN=float(os.environ.get("STICKERNEST_VISUAL_BALANCE_MIN","0.96"))
VISUAL_MAX=float(os.environ.get("STICKERNEST_VISUAL_BALANCE_MAX","1.10"))
UNIT_EQ=[unit_alpha_eq(m) for _,m in raw]
MED_EQ=float(np.median(np.array(UNIT_EQ))) if UNIT_EQ else 1.0
VISUAL_BASE=[max(VISUAL_MIN,min(VISUAL_MAX,(MED_EQ/e)**VISUAL_POWER)) for e in UNIT_EQ]
SCALE_LO=[max(0.84,b*0.92) for b in VISUAL_BASE]
SCALE_HI=[min(1.30,max(1.02,b*1.08)) for b in VISUAL_BASE]

def clamp_scale(i,sc):
    return max(SCALE_LO[i], min(SCALE_HI[i], float(sc)))

def candidate_scales(i):
    vals=[clamp_scale(i,VISUAL_BASE[i]*f) for f in (0.94,0.98,1.0,1.04,1.08)]
    return sorted(set(round(v,4) for v in vals))

def dil(m,r):
    out=m.copy()
    for _ in range(r):o=out.copy();o[1:]|=out[:-1];o[:-1]|=out[1:];o[:,1:]|=out[:,:-1];o[:,:-1]|=out[:,1:];out=o
    return out
def dil_square(m,r):
    if r<=0:
        return m.copy()
    kernel=np.ones((2*r+1,2*r+1),np.uint8)
    return cv2.dilate(m.astype(np.uint8),kernel,iterations=1).astype(bool)
def mask_runs(m):
    runs=[]
    for y,row in enumerate(m):
        xs=np.flatnonzero(row)
        if xs.size==0:
            continue
        start=int(xs[0]); prev=start
        for value in xs[1:]:
            value=int(value)
            if value==prev+1:
                prev=value
            else:
                runs.append({"y":int(y),"x0":start,"x1":prev+1})
                start=value; prev=value
        runs.append({"y":int(y),"x0":start,"x1":prev+1})
    return runs
cache={}
def make(i,ang,sc,gap=True):
    sc=clamp_scale(i,sc)
    k=(i,ang,round(sc,3),gap)
    if k in cache:return cache[k]
    m=raw[i][1].astype(np.uint8)*255;h,w=m.shape;f=BASE*sc/max(h,w)
    m=cv2.resize(m,(max(1,int(w*f)),max(1,int(h*f))),interpolation=cv2.INTER_AREA)
    if ang%360:
        hh,ww=m.shape;M=cv2.getRotationMatrix2D((ww/2,hh/2),ang,1.0)
        cosA,sinA=abs(M[0,0]),abs(M[0,1]);nW=int(hh*sinA+ww*cosA);nH=int(hh*cosA+ww*sinA)
        M[0,2]+=nW/2-ww/2;M[1,2]+=nH/2-hh/2;m=cv2.warpAffine(m,M,(nW,nH))
    mm=m>120
    if gap:
        padded=np.pad(mm, ((G,G),(G,G)), mode="constant", constant_values=False)
        r=dil_square(padded,G)
    else:
        r=mm
    cache[k]=r;return r
def corr(field,m):
    H,W=field.shape;h,w=m.shape
    return irfft2(rfft2(field.astype(np.float32),s=(H,W))*rfft2(m[::-1,::-1].astype(np.float32),s=(H,W)),s=(H,W))[h-1:H,w-1:W]
def place(occ,m):
    H,W=occ.shape;h,w=m.shape
    if h>H or w>W:return None
    valid=corr(occ,m)<0.5
    if not valid.any():return None
    wall=dil(occ,1)&(~occ);wall[0,:]=True;wall[-1,:]=True;wall[:,0]=True;wall[:,-1]=True
    sc=corr(wall,m).astype(float)+(np.arange(valid.shape[0])[:,None])*Y_BIAS
    sc[~valid]=-1e18;y,x=np.unravel_index(np.argmax(sc),sc.shape);return int(x),int(y)

def place_guided(occ,m,target_x,target_y,row_strength=1.0):
    H,W=occ.shape;h,w=m.shape
    if h>H or w>W:return None
    valid=corr(occ,m)<0.5
    if not valid.any():return None
    wall=dil(occ,1)&(~occ);wall[0,:]=True;wall[-1,:]=True;wall[:,0]=True;wall[:,-1]=True
    contact=corr(wall,m).astype(float)
    ys=np.arange(valid.shape[0])[:,None]
    xs=np.arange(valid.shape[1])[None,:]
    dx=np.abs(xs-float(target_x))
    dy=np.abs(ys-float(target_y))
    # Human sheets start from row/slot intuition, then slide to contact. Keep the
    # slot pull soft so geometry can still win when a nearby cavity is better.
    sc=contact*1.25 - dx*(0.025*row_strength) - dy*(0.055*row_strength) - ys*0.015
    sc[~valid]=-1e18
    y,x=np.unravel_index(np.argmax(sc),sc.shape);return int(x),int(y)

def stamp(occ,x,y,m):
    occ[y:y+m.shape[0],x:x+m.shape[1]]|=m

def build_occ(pl, skip=None):
    skip=skip or set()
    occ=BASE_OCC.copy()
    for i,x,y,r,s in pl:
        if i in skip: continue
        stamp(occ,x,y,make(i,r,s))
    return occ

def decode(order,rots,scs):
    occ=BASE_OCC.copy();pl=[]
    for idx in order:
        m=make(idx,rots[idx],scs[idx]);p=place(occ,m)
        if p is None:return None
        x,y=p;stamp(occ,x,y,m);pl.append((idx,x,y,rots[idx],scs[idx]))
    return pl

def decode_human_slots(order,rots,scs,rows=HUMAN_ROWS,cols=HUMAN_COLS):
    occ=BASE_OCC.copy();pl=[]
    edge=max(EDGE_BLOCK+G,2)
    usable_w=max(1,SW-edge*2)
    usable_h=max(1,SH-edge*2)
    for pos,idx in enumerate(order):
        m=make(idx,rots[idx],scs[idx])
        row=min(rows-1,pos//max(1,cols))
        col=pos%max(1,cols)
        target_x=edge+(col+0.5)*usable_w/max(1,cols)-m.shape[1]/2
        target_y=edge+(row+0.5)*usable_h/max(1,rows)-m.shape[0]/2
        p=place_guided(occ,m,target_x,target_y,row_strength=1.0)
        if p is None:
            p=place(occ,m)
        if p is None:return None
        x,y=p;stamp(occ,x,y,m);pl.append((idx,x,y,rots[idx],scs[idx]))
    return pl

def stagger_templates(limit=10):
    if not MANUAL_STAGGER or not isinstance(STAGGER_POLICY,dict):
        return []
    if STAGGER_POLICY.get("item_count") not in (None,N):
        return []
    templates=STAGGER_POLICY.get("templates")
    if not isinstance(templates,list):
        return []
    usable=[t for t in templates if isinstance(t,dict) and isinstance(t.get("slots"),list) and len(t.get("slots"))>=N]
    if not usable:
        return []
    high=sorted(usable,key=lambda t:float(t.get("row_spread_mm_mean",0.0)),reverse=True)
    middle=sorted(usable,key=lambda t:abs(float(t.get("row_spread_mm_mean",0.0))-33.0))
    out=[]
    for t in high[:max(2,limit//2)]+middle[:max(2,limit//2)]:
        if t not in out:
            out.append(t)
        if len(out)>=limit:
            break
    return out

def manual_rotation_seed(order,variant=0):
    rots=[0 for _ in range(N)]
    if not (MANUAL_STAGGER and MANUAL_STAGGER_ROTATE):
        return rots
    patterns=[
        [0,0,0,0,0],
        [0,180,0,0,0],
        [0,0,180,0,0],
        [0,90,0,0,180],
        [0,0,270,0,0],
        [0,0,180,0,180],
    ]
    pattern=patterns[variant%len(patterns)]
    for pos,idx in enumerate(order):
        row=pos//max(1,HUMAN_COLS)
        col=pos%max(1,HUMAN_COLS)
        angle=pattern[(col+row*(variant%3))%len(pattern)]
        if angle in ANG:
            rots[idx]=angle
    return rots

def decode_stagger_template(order,rots,scs,template):
    if not MANUAL_STAGGER or N!=HUMAN_ROWS*HUMAN_COLS:
        return None
    slots=template.get("slots") if isinstance(template,dict) else None
    if not isinstance(slots,list):
        return None
    by={}
    for slot in slots:
        try:
            by[(int(slot["row"]),int(slot["col"]))]=slot
        except Exception:
            pass
    if len(by)<N:
        return None
    occ=BASE_OCC.copy();pl=[]
    edge=max(EDGE_BLOCK+G,2)
    usable_w=max(1,SW-edge*2)
    usable_h=max(1,SH-edge*2)
    for pos,idx in enumerate(order):
        m=make(idx,rots[idx],scs[idx])
        row=min(HUMAN_ROWS-1,pos//max(1,HUMAN_COLS))
        col=pos%max(1,HUMAN_COLS)
        slot=by.get((row,col),{})
        target_x=edge+(col+0.5)*usable_w/max(1,HUMAN_COLS)-m.shape[1]/2
        target_y=edge+(row+0.5)*usable_h/max(1,HUMAN_ROWS)-m.shape[0]/2
        target_x+=csigned(float(slot.get("dx_mm",0.0))*MANUAL_STAGGER_STRENGTH)
        target_y+=csigned(float(slot.get("dy_row_mm",0.0))*MANUAL_STAGGER_STRENGTH)
        target_x=min(max(0,target_x),max(0,SW-m.shape[1]))
        target_y=min(max(0,target_y),max(0,SH-m.shape[0]))
        p=place_guided(occ,m,target_x,target_y,row_strength=1.25)
        if p is None:
            p=place(occ,m)
        if p is None:return None
        x,y=p;stamp(occ,x,y,m);pl.append((idx,x,y,rots[idx],scs[idx]))
    return pl

def decode_trace(order,rots,scs,rounds=3):
    occ=BASE_OCC.copy();pl=[];pending=list(order);placed=set()
    for _ in range(rounds):
        if not pending: break
        next_pending=[];progress=0
        for idx in pending:
            if idx in placed: continue
            m=make(idx,rots[idx],scs[idx]);p=place(occ,m)
            if p is None:
                next_pending.append(idx);continue
            x,y=p;stamp(occ,x,y,m);pl.append((idx,x,y,rots[idx],scs[idx]));placed.add(idx);progress+=1
        pending=next_pending
        if progress==0: break
    return pl,pending,occ

def uniq(vals):
    out=[]
    for v in vals:
        if v not in out: out.append(v)
    return out

def local_angle_candidates(base,broad=False):
    if MANUAL_STAGGER:
        vals=[base,0,8,352,12,348,15,345,30,330]
        if not MANUAL_STAGGER_SAFE_ROTATE:
            vals.extend([180,90,270])
        if broad and not MANUAL_STAGGER_SAFE_ROTATE:
            vals.extend([75,105,255,285])
    else:
        vals=[base,0,15,345,12,348,30,330]
    return [v for v in uniq([int(v)%360 for v in vals]) if v in ANG or v==base]

def angle_variants(i,base):
    return local_angle_candidates(base,broad=True)

def scale_variants(i,base,missing=False):
    factors=[1.0,0.99,0.98,0.965,1.01,1.02] if missing else [1.0,0.99,0.98,0.965,0.95]
    return uniq([round(clamp_scale(i,base*f),4) for f in factors])

def item_variants(i,base_r,base_s,missing=False):
    pairs=[]
    for r in angle_variants(i,base_r):
        angle_delta=min((int(r)-int(base_r))%360,(int(base_r)-int(r))%360)
        for s in scale_variants(i,base_s,missing=missing):
            scale_penalty=abs(float(s)-float(base_s))
            size_bonus=-float(s) if missing else float(s)
            pairs.append((angle_delta, scale_penalty, size_bonus, int(r)%360, float(s)))
    pairs.sort()
    return [(r,round(s,4)) for _,_,_,r,s in pairs[:RECOVERY_MULTI_MAX_VARIANTS]]

def try_sequence(base,occ,seq):
    if not seq:
        return base
    idx,base_r,base_s,is_missing=seq[0]
    for r,s in item_variants(idx,base_r,base_s,missing=is_missing):
        m=make(idx,r,s);p=place(occ,m)
        if p is None:
            continue
        occ2=occ.copy();stamp(occ2,p[0],p[1],m)
        res=try_sequence(base+[(idx,p[0],p[1],r,s)],occ2,seq[1:])
        if res is not None:
            return res
    return None

def order_variants(indices):
    variants=[list(indices),list(reversed(indices)),sorted(indices,key=lambda i:-raw[i][1].sum()),sorted(indices,key=lambda i:raw[i][1].sum())]
    if len(indices)<=3:
        variants.extend([list(p) for p in itertools.permutations(indices)])
    out=[]
    for v in variants:
        if v not in out:
            out.append(v)
    return out

def recovery_blocker_combos(pl,pending,rots,scs):
    scored=[];seen=set()
    for rank,(i,_,_,_,_) in enumerate(reversed(pl)):
        if i in seen:
            continue
        seen.add(i)
        score=0
        if rank<8:
            score+=1
        occ=build_occ(pl,skip={i})
        for miss in pending:
            for r,s in item_variants(miss,rots[miss],scs[miss],missing=True)[:6]:
                if place(occ,make(miss,r,s)) is not None:
                    score+=3
                    break
        if score>0:
            scored.append((score,-rank,i))
    ids=[i for _,_,i in sorted(scored,reverse=True)[:10]]
    combos=[]
    max_blockers=min(RECOVERY_MULTI_MAX_BLOCKERS,len(ids))
    for size in range(1,max_blockers+1):
        for combo in itertools.combinations(ids,size):
            combos.append(combo)
            if len(combos)>=RECOVERY_MULTI_MAX_COMBOS:
                return combos
    return combos

def recover_24_plus_1(order,rots,scs):
    if not RECOVERY_24P1 or BASE_MM < RECOVERY_MIN_TARGET:
        return None
    pl,pending,_=decode_trace(order,rots,scs,RECOVERY_TRACE_ROUNDS)
    if RECOVERY_DEBUG:
        print(f"recovery_trace target={BASE_MM:.1f} placed={len(pl)}/{N} pending={','.join(raw[i][0] for i in pending[:5])}", file=sys.stderr)
    if len(pending)!=1 or len(pl)!=N-1:
        return None
    missing=pending[0]
    blockers=[]
    for i,x,y,r,s in reversed(pl):
        occ=build_occ(pl,skip={i})
        found=False
        for mr in angle_variants(missing,rots[missing]):
            for ms in scale_variants(missing,scs[missing],missing=True):
                if place(occ,make(missing,mr,ms)) is not None:
                    found=True;break
            if found:break
        if found:
            blockers.append(i)
            if len(blockers)>=RECOVERY_MAX_BLOCKERS: break
    for blocker in blockers:
        base=[entry for entry in pl if entry[0]!=blocker]
        occ=build_occ(base)
        for mr in angle_variants(missing,rots[missing]):
            for ms in scale_variants(missing,scs[missing],missing=True):
                mm=make(missing,mr,ms);pm=place(occ,mm)
                if pm is None: continue
                occ2=occ.copy();stamp(occ2,pm[0],pm[1],mm)
                for br in angle_variants(blocker,rots[blocker]):
                    for bs in scale_variants(blocker,scs[blocker],missing=False):
                        bm=make(blocker,br,bs);pb=place(occ2,bm)
                        if pb is not None:
                            return base+[(missing,pm[0],pm[1],mr,ms),(blocker,pb[0],pb[1],br,bs)]
    return None

def recover_multi_missing(order,rots,scs):
    if not RECOVERY_MULTI or BASE_MM < RECOVERY_MULTI_MIN_TARGET:
        return None
    pl,pending,_=decode_trace(order,rots,scs,RECOVERY_TRACE_ROUNDS)
    if RECOVERY_DEBUG:
        print(f"recovery_multi_trace target={BASE_MM:.1f} placed={len(pl)}/{N} pending={','.join(raw[i][0] for i in pending[:5])}", file=sys.stderr)
    if len(pending)<2 or len(pending)>RECOVERY_MULTI_MAX_PENDING:
        return None
    if len(pl)+len(pending)!=N:
        return None
    combos=recovery_blocker_combos(pl,pending,rots,scs)
    for combo in combos:
        blockers=set(combo)
        base=[entry for entry in pl if entry[0] not in blockers]
        blocker_entries=[entry for entry in pl if entry[0] in blockers]
        if not blocker_entries:
            continue
        occ=build_occ(base)
        blocker_orders=[blocker_entries,list(reversed(blocker_entries))]
        for miss_order in order_variants(pending):
            missing_seq=[(idx,rots[idx],scs[idx],True) for idx in miss_order]
            placed_missing=try_sequence(base,occ.copy(),missing_seq)
            if placed_missing is None:
                continue
            occ_missing=build_occ(placed_missing)
            for blocker_order in blocker_orders:
                blocker_seq=[(i,r,s,False) for i,_,_,r,s in blocker_order]
                recovered=try_sequence(placed_missing,occ_missing.copy(),blocker_seq)
                if recovered is not None and len(recovered)==N:
                    return recovered
    return None

def decode_initial(order,rots,scs):
    pl=decode(order,rots,scs)
    if pl is not None:
        return pl
    pl=recover_24_plus_1(order,rots,scs)
    if pl is not None:
        return pl
    return recover_multi_missing(order,rots,scs)

def ink(pl):
    o=np.zeros((SH,SW),bool)
    for i,x,y,r,s in pl:
        m=make(i,r,s,gap=False);o[y:y+m.shape[0],x:x+m.shape[1]]|=m
    return o.sum()/(SW*SH)

def gap_occupancy(pl):
    o=BASE_OCC.copy()
    for i,x,y,r,s in pl:
        m=make(i,r,s,gap=True)
        yb=min(SH,y+m.shape[0]);xb=min(SW,x+m.shape[1])
        if yb>y and xb>x:o[y:yb,x:xb]|=m[:yb-y,:xb-x]
    return o

def content_occupancy(pl):
    o=np.zeros((SH,SW),bool)
    for i,x,y,r,s in pl:
        m=make(i,r,s,gap=False)
        y0=y+G;x0=x+G;y1=min(SH,y0+m.shape[0]);x1=min(SW,x0+m.shape[1])
        if y1>y0 and x1>x0:o[y0:y1,x0:x1]|=m[:y1-y0,:x1-x0]
    return o

def blank_fraction(occ,x0,y0,x1,y1):
    x0=max(0,int(x0));y0=max(0,int(y0));x1=min(SW,int(x1));y1=min(SH,int(y1))
    if x1<=x0 or y1<=y0:return 1.0
    region=occ[y0:y1,x0:x1]
    allowed=(~BASE_OCC[y0:y1,x0:x1])
    denom=max(1,int(allowed.sum()))
    return 1.0-float((region&allowed).sum())/denom

def row_column_imbalance(pl):
    if not pl:return 1.0
    rows=[0]*HUMAN_ROWS;cols=[0]*HUMAN_COLS
    for i,x,y,r,s in pl:
        m=make(i,r,s,gap=True)
        cx=(x+m.shape[1]/2)/max(1,SW);cy=(y+m.shape[0]/2)/max(1,SH)
        rows[min(HUMAN_ROWS-1,max(0,int(cy*HUMAN_ROWS)))] += 1
        cols[min(HUMAN_COLS-1,max(0,int(cx*HUMAN_COLS)))] += 1
    ideal_r=len(pl)/max(1,HUMAN_ROWS);ideal_c=len(pl)/max(1,HUMAN_COLS)
    rb=sum(abs(v-ideal_r) for v in rows)/max(1.0,len(pl))
    cb=sum(abs(v-ideal_c) for v in cols)/max(1.0,len(pl))
    return (rb+cb)*0.5

def policy_slots_5x5():
    slots=MANUAL_POLICY.get("slots_5x5") if isinstance(MANUAL_POLICY,dict) else None
    if isinstance(slots,list) and len(slots)>=HUMAN_ROWS*HUMAN_COLS:
        by={}
        for slot in slots:
            try:
                by[(int(slot["row"]),int(slot["col"]))]=(float(slot["x"]),float(slot["y"]))
            except Exception:
                pass
        if len(by)>=HUMAN_ROWS*HUMAN_COLS:
            return by
    return {
        (r,c):((c+0.5)/HUMAN_COLS,(r+0.5)/HUMAN_ROWS)
        for r in range(HUMAN_ROWS) for c in range(HUMAN_COLS)
    }

POLICY_SLOTS=policy_slots_5x5()

def row_bins(pl):
    rows=[[] for _ in range(HUMAN_ROWS)]
    for k,(i,x,y,r,s) in enumerate(pl):
        m=make(i,r,s,gap=True)
        cx=(x+m.shape[1]/2)/max(1,SW)
        cy=(y+m.shape[0]/2)/max(1,SH)
        ri=min(HUMAN_ROWS-1,max(0,int(cy*HUMAN_ROWS)))
        rows[ri].append((k,cx,cy,m.shape[1],m.shape[0]))
    return rows

def target_row_counts(n):
    base=n//HUMAN_ROWS
    rem=n%HUMAN_ROWS
    counts=[base]*HUMAN_ROWS
    for r in range(rem):
        counts[r]+=1
    return counts

def layout_metrics(pl):
    g=gap_occupancy(pl)
    center_blank=blank_fraction(g,SW*0.18,SH*0.16,SW*0.82,SH*0.86)
    lower_blank=blank_fraction(g,SW*0.06,SH*0.62,SW*0.94,SH*0.96)
    large_blank=0.0
    for ty in range(8):
        for tx in range(10):
            large_blank=max(large_blank,blank_fraction(g,SW*tx/10,SH*ty/8,SW*(tx+1)/10,SH*(ty+1)/8))
    return {
        "alpha":ink(pl),
        "center_blank":center_blank,
        "lower_blank":lower_blank,
        "large_blank":large_blank,
        "imbalance":row_column_imbalance(pl),
        "quality":layout_quality(pl),
    }

def missing_policy_slots(row_entries,row_index):
    present=[entry[1] for entry in row_entries]
    candidates=[]
    for col in range(HUMAN_COLS):
        sx,sy=POLICY_SLOTS.get((row_index,col),((col+0.5)/HUMAN_COLS,(row_index+0.5)/HUMAN_ROWS))
        nearest=min([abs(px-sx) for px in present], default=1.0)
        candidates.append((nearest,sx,sy,col))
    candidates.sort(reverse=True)
    return candidates

def manual_row_rebalance(pl, rounds=1):
    if not MANUAL_ROW_REBALANCE or N != HUMAN_ROWS*HUMAN_COLS:
        return pl
    pl=pl[:]
    for _ in range(rounds):
        rows=row_bins(pl)
        ideal=target_row_counts(len(pl))
        over=[r for r in range(HUMAN_ROWS) if len(rows[r])>ideal[r]]
        under=[r for r in range(HUMAN_ROWS-1,-1,-1) if len(rows[r])<ideal[r]]
        if not over or not under:
            break
        before=layout_metrics(pl)
        accepted=False
        for target_row in under:
            for source_row in over:
                if source_row==target_row:
                    continue
                # Move smaller/easier pieces first. This mirrors manual fill-in:
                # keep the row structure, then use a flexible figure to occupy
                # the missing lower slot.
                movable=sorted(rows[source_row], key=lambda e:make(pl[e[0]][0],pl[e[0]][3],pl[e[0]][4],gap=False).sum())
                for _,slot_x,slot_y,_ in missing_policy_slots(rows[target_row],target_row)[:2]:
                    for k,_,_,_,_ in movable[:4]:
                        i,x,y,r,s=pl[k]
                        base=[entry for j,entry in enumerate(pl) if j!=k]
                        occ=BASE_OCC.copy()
                        for ii,xx,yy,rr,ss in base:
                            stamp(occ,xx,yy,make(ii,rr,ss,gap=True))
                        variants=[]
                        for rr in local_angle_candidates(r,broad=MANUAL_STAGGER):
                            for ss in [s,clamp_scale(i,s*0.99),clamp_scale(i,s*0.975),clamp_scale(i,s*1.01)]:
                                pair=(int(rr)%360,round(ss,4))
                                if pair not in variants:
                                    variants.append(pair)
                        for rr,ss in variants[:18 if MANUAL_STAGGER else 10]:
                            mm=make(i,rr,ss,gap=True)
                            tx=slot_x*SW-mm.shape[1]/2
                            ty=slot_y*SH-mm.shape[0]/2
                            p=place_guided(occ,mm,tx,ty,row_strength=1.85)
                            if p is None:
                                continue
                            trial=base+[(i,p[0],p[1],rr,ss)]
                            after=layout_metrics(trial)
                            row_gain=before["imbalance"]-after["imbalance"]
                            lower_gain=before["lower_blank"]-after["lower_blank"]
                            large_gain=before["large_blank"]-after["large_blank"]
                            alpha_ok=after["alpha"]>=before["alpha"]-0.0015
                            blank_ok=lower_gain>=0.018 or large_gain>=0.035
                            center_ok=after["center_blank"]<=before["center_blank"]+0.018
                            quality_ok=after["quality"]>=before["quality"]-0.010 or after["alpha"]>=before["alpha"]+0.0025
                            if alpha_ok and blank_ok and center_ok and quality_ok and row_gain>=0.025:
                                pl=trial
                                accepted=True
                                if RECOVERY_DEBUG:
                                    print(f"manual_row_rebalance sourceRow={source_row} targetRow={target_row} item={raw[i][0]} rowGain={row_gain:.3f} lowerGain={lower_gain:.3f} largeGain={large_gain:.3f} alpha={after['alpha']*100:.1f}%", file=sys.stderr)
                                break
                        if accepted:
                            break
                    if accepted:
                        break
                if accepted:
                    break
            if accepted:
                break
        if not accepted:
            break
    return pl

def place_near(occ,m,cx,cy,radius_cells=20):
    H,W=occ.shape;h,w=m.shape
    if h>H or w>W:return None
    base_x=int(round(cx-w/2));base_y=int(round(cy-h/2))
    best=None;best_score=None
    for radius in [0,3,6,10,14,radius_cells]:
        step=max(1,radius//4)
        for dy in range(-radius,radius+1,step):
            for dx in range(-radius,radius+1,step):
                if radius and abs(dx)!=radius and abs(dy)!=radius:
                    continue
                x=min(max(0,base_x+dx),W-w);y=min(max(0,base_y+dy),H-h)
                region=occ[y:y+h,x:x+w]
                if region.shape!=m.shape or region[m].any():
                    continue
                wall=dil(occ,1)&(~occ)
                contact=0
                sub=wall[y:y+h,x:x+w]
                if sub.shape==m.shape:
                    contact=int((sub&m).sum())
                dist=abs(x-base_x)+abs(y-base_y)
                score=dist-contact*0.08
                if best is None or score<best_score:
                    best=(x,y);best_score=score
        if best is not None and radius>=6:
            break
    return best

def micro_refit(pl, rounds=1):
    if not MICRO_REFIT:
        return pl
    pl=pl[:]
    for _ in range(rounds):
        improved=False
        before=layout_metrics(pl)
        order=sorted(range(len(pl)), key=lambda k:-make(pl[k][0],pl[k][3],pl[k][4],gap=True).sum())
        for k in order:
            i,x,y,r,s=pl[k]
            old=make(i,r,s,gap=True)
            cx=x+old.shape[1]/2;cy=y+old.shape[0]/2
            base=[entry for j,entry in enumerate(pl) if j!=k]
            occ=BASE_OCC.copy()
            for ii,xx,yy,rr,ss in base:
                stamp(occ,xx,yy,make(ii,rr,ss,gap=True))
            variants=[]
            for rr in local_angle_candidates(r,broad=MANUAL_STAGGER):
                for ss in [s]:
                    pair=(int(rr)%360,round(ss,4))
                    if pair not in variants:
                        variants.append(pair)
            best_trial=None;best_metrics=None
            for rr,ss in variants[:24 if MANUAL_STAGGER else 14]:
                if rr==r and abs(ss-s)<0.0005:
                    continue
                mm=make(i,rr,ss,gap=True)
                p=place_near(occ,mm,cx,cy,radius_cells=24)
                if p is None:
                    continue
                trial=base+[(i,p[0],p[1],rr,ss)]
                after=layout_metrics(trial)
                alpha_ok=after["alpha"]>=before["alpha"]-0.0005
                blank_gain=(before["center_blank"]-after["center_blank"])*0.60+(before["lower_blank"]-after["lower_blank"])*0.80+(before["large_blank"]-after["large_blank"])*0.35
                size_ok=size_cv(trial)<=size_cv(pl)+0.0015
                center_ok=after["center_blank"]<=before["center_blank"]+0.002
                lower_or_large_ok=(before["lower_blank"]-after["lower_blank"]>=0.010) or (before["large_blank"]-after["large_blank"]>=0.020)
                quality_ok=after["quality"]>=before["quality"]+0.004 or (blank_gain>=0.010 and after["quality"]>=before["quality"]-0.002)
                if alpha_ok and size_ok and center_ok and lower_or_large_ok and quality_ok:
                    if best_metrics is None or after["quality"]>best_metrics["quality"]:
                        best_trial=trial;best_metrics=after
            if best_trial is not None:
                pl=best_trial
                improved=True
                if RECOVERY_DEBUG:
                    print(f"micro_refit item={raw[i][0]} alpha={best_metrics['alpha']*100:.1f}% centerBlank={best_metrics['center_blank']:.3f} lowerBlank={best_metrics['lower_blank']:.3f}", file=sys.stderr)
                break
        if not improved:
            break
    return pl

def size_cv(pl):
    vals=[]
    for i,_,_,r,s in pl:
        m=make(i,r,s,gap=False);vals.append(math.sqrt(max(1,int(m.sum()))))
    if len(vals)<2:return 0.0
    mean=sum(vals)/len(vals)
    return (sum((v-mean)**2 for v in vals)/len(vals))**0.5/max(1e-6,mean)

def orientation_bucket(angle):
    a=int(angle)%360
    delta=min(a,360-a)
    if delta<=20:
        return "upright" if delta<5 else "small"
    if 160<=a<=200:
        return "upside"
    if 70<=a<=110 or 250<=a<=290:
        return "sideways"
    if delta>=45:
        return "hard"
    return "small"

def orientation_stats(pl):
    counts={"upright":0,"small":0,"upside":0,"sideways":0,"hard":0}
    for _,_,_,r,_ in pl or []:
        bucket=orientation_bucket(r)
        counts[bucket]=counts.get(bucket,0)+1
    n=max(1,len(pl or []))
    hard_total=counts["upside"]+counts["sideways"]+counts["hard"]
    varied=hard_total+counts["small"]
    readable=counts["upright"]+counts["small"]
    return {
        "upright":counts["upright"],
        "small":counts["small"],
        "upside":counts["upside"],
        "sideways":counts["sideways"],
        "hard_other":counts["hard"],
        "hard":hard_total,
        "varied":varied,
        "readable":readable,
        "upright_ratio":counts["upright"]/n,
        "small_ratio":counts["small"]/n,
        "upside_ratio":counts["upside"]/n,
        "sideways_ratio":counts["sideways"]/n,
        "hard_other_ratio":counts["hard"]/n,
        "hard_ratio":hard_total/n,
        "varied_ratio":varied/n,
        "readable_ratio":readable/n,
    }

def angle_histogram(pl):
    hist={}
    for _,_,_,r,_ in pl or []:
        key=str(int(r)%360)
        hist[key]=hist.get(key,0)+1
    return {k:hist[k] for k in sorted(hist,key=lambda v:int(v))}

def row_orientation_stats(pl):
    rows=[{"upright":0,"small":0,"upside":0,"sideways":0,"hard_other":0,"hard":0,"readable":0,"count":0} for _ in range(HUMAN_ROWS)]
    for i,x,y,r,s in pl or []:
        m=make(i,r,s,gap=True)
        cy=(y+m.shape[0]/2)/max(1,SH)
        row=min(HUMAN_ROWS-1,max(0,int(cy*HUMAN_ROWS)))
        bucket=orientation_bucket(r)
        key="hard_other" if bucket=="hard" else bucket
        rows[row][key]+=1
        rows[row]["count"]+=1
    for row in rows:
        row["hard"]=row["upside"]+row["sideways"]+row["hard_other"]
        row["readable"]=row["upright"]+row["small"]
    return rows

def orientation_readability_score(pl):
    if not READABILITY_GUARD or not pl:
        return 0.0
    s=orientation_stats(pl)
    penalty=0.0
    penalty+=max(0.0,MIN_READABLE_RATIO-s["readable_ratio"])*0.90
    penalty+=max(0.0,MIN_UPRIGHT_RATIO-s["upright_ratio"])*0.55
    penalty+=max(0.0,s["upside_ratio"]-MAX_UPSIDE_RATIO)*1.15
    penalty+=max(0.0,s["sideways_ratio"]-MAX_SIDEWAYS_RATIO)*0.95
    penalty+=max(0.0,s["hard_other_ratio"]-MAX_HARD_OTHER_RATIO)*0.85
    penalty+=max(0.0,s["hard_ratio"]-MAX_HARD_ROTATION_RATIO)*1.05
    reward=0.0
    if 0.12<=s["upside_ratio"]<=MAX_UPSIDE_RATIO and s["sideways_ratio"]<=MAX_SIDEWAYS_RATIO:
        reward+=0.035
    if s["readable_ratio"]>=MIN_READABLE_RATIO and s["hard_ratio"]<=MAX_HARD_ROTATION_RATIO:
        reward+=0.025
    return reward-penalty

def density_readability_balance_score(pl, alpha):
    if not READABILITY_GUARD or not pl:
        return 0.0
    s=orientation_stats(pl)
    # Once a layout is already readable, do not let marginal readability gains
    # choose a weak-density candidate that would fail the app accept-alpha floor.
    if s["readable_ratio"]>=0.68 and s["hard"]<=7 and s["upside_ratio"]<=0.28:
        floor=0.500
        return min(0.12,max(0.0,alpha-floor)*8.0) - max(0.0,floor-alpha)*8.0
    return 0.0

def orientation_hard_reject(pl):
    if not READABILITY_GUARD or not MANUAL_STAGGER or not pl:
        return False
    s=orientation_stats(pl)
    if s["upside_ratio"]>HARD_REJECT_UPSIDE_RATIO:
        return True
    if s["sideways_ratio"]>HARD_REJECT_SIDEWAYS_RATIO:
        return True
    if s["hard_ratio"]>HARD_REJECT_HARD_RATIO:
        return True
    if s["readable_ratio"]<HARD_REJECT_MIN_READABLE_RATIO:
        return True
    for row in row_orientation_stats(pl):
        if row["count"]>=4 and row["readable"]==0:
            return True
        if row["count"]>=5 and row["hard"]>=5:
            return True
    return False

def orientation_thresholds():
    return {
        "min_readable_ratio":MIN_READABLE_RATIO,
        "min_upright_ratio":MIN_UPRIGHT_RATIO,
        "max_upside_ratio":MAX_UPSIDE_RATIO,
        "max_sideways_ratio":MAX_SIDEWAYS_RATIO,
        "max_hard_other_ratio":MAX_HARD_OTHER_RATIO,
        "max_hard_rotation_ratio":MAX_HARD_ROTATION_RATIO,
        "hard_reject_upside_ratio":HARD_REJECT_UPSIDE_RATIO,
        "hard_reject_sideways_ratio":HARD_REJECT_SIDEWAYS_RATIO,
        "hard_reject_hard_ratio":HARD_REJECT_HARD_RATIO,
        "hard_reject_min_readable_ratio":HARD_REJECT_MIN_READABLE_RATIO,
    }

def manual_pose_score(pl):
    if not MANUAL_STAGGER or not pl:
        return 0.0
    stats=orientation_stats(pl)
    hard_ratio=stats["hard_ratio"]
    varied_ratio=stats["varied_ratio"]
    reward=min(hard_ratio,0.34)*0.36 + min(varied_ratio,0.56)*0.10
    if stats["hard"]==0 and stats["varied"]<3:
        reward-=0.10
    return reward + orientation_readability_score(pl)

def layout_quality(pl):
    if pl is None:return -1e9
    if orientation_hard_reject(pl):
        return -1e9
    alpha=ink(pl)
    g=gap_occupancy(pl)
    ys,xs=np.where(g & (~BASE_OCC))
    bbox=0.0
    if len(xs)>0 and len(ys)>0:
        bbox=((xs.max()-xs.min()+1)*(ys.max()-ys.min()+1))/(SW*SH)
    center_blank=blank_fraction(g,SW*0.18,SH*0.16,SW*0.82,SH*0.86)
    lower_blank=blank_fraction(g,SW*0.06,SH*0.62,SW*0.94,SH*0.96)
    large_blank=0.0
    for ty in range(8):
        for tx in range(10):
            large_blank=max(large_blank,blank_fraction(g,SW*tx/10,SH*ty/8,SW*(tx+1)/10,SH*(ty+1)/8))
    imbalance=row_column_imbalance(pl)
    cv=size_cv(pl)
    # Keep alpha important, but make visibly empty middle/lower cavities decide
    # between same-alpha layouts. This is the first true human-style objective.
    return alpha*6.0 + bbox*0.65 - center_blank*1.20 - lower_blank*1.65 - large_blank*0.35 - imbalance*0.22 - cv*0.18 + manual_pose_score(pl) + density_readability_balance_score(pl,alpha)

def row_phase_order_sets(base):
    if not ROW_PHASE_BASE_PROBE or len(base)!=N or N!=HUMAN_ROWS*HUMAN_COLS:
        return []
    areas={i:float(raw[i][1].sum()) for i in base}
    heights={i:int(raw[i][1].shape[0]) for i in base}
    widths={i:int(raw[i][1].shape[1]) for i in base}

    def balanced_rows(items):
        rows=[[] for _ in range(HUMAN_ROWS)]
        row_area=[0.0 for _ in range(HUMAN_ROWS)]
        for idx in sorted(items,key=lambda i:(areas[i],heights[i]),reverse=True):
            row=min(range(HUMAN_ROWS),key=lambda r:(row_area[r],len(rows[r])))
            rows[row].append(idx)
            row_area[row]+=areas[idx]
        return rows

    def flatten_rows(rows,snake=False):
        out=[]
        for row_index,row in enumerate(rows):
            ordered=sorted(row,key=lambda i:(-heights[i],widths[i],-areas[i]))
            if snake and row_index%2:
                ordered=list(reversed(ordered))
            out.extend(ordered)
        return out

    rows=balanced_rows(base)
    row_area_order=flatten_rows(rows,snake=False)
    row_area_snake=flatten_rows(rows,snake=True)

    tall_first=sorted(base,key=lambda i:(-heights[i],-areas[i],widths[i]))
    tall_rows=[tall_first[r::HUMAN_ROWS] for r in range(HUMAN_ROWS)]
    tall_phase_snake=flatten_rows(tall_rows,snake=True)

    wide_first=sorted(base,key=lambda i:(-widths[i],-areas[i],heights[i]))
    wide_rows=[wide_first[r::HUMAN_ROWS] for r in range(HUMAN_ROWS)]
    wide_phase_snake=flatten_rows(wide_rows,snake=True)

    out=[]
    for label,order in [
        ("row_phase_area",row_area_order),
        ("row_phase_area_snake",row_area_snake),
        ("row_phase_tall_snake",tall_phase_snake),
        ("row_phase_wide_snake",wide_phase_snake),
    ]:
        if len(order)==N and sorted(order)==sorted(base) and order not in [o for _,o in out]:
            out.append((label,order))
    return out

def human_seed_layouts():
    if not (HUMAN_IMITATION or MANUAL_STAGGER) or N==0:
        return []
    base=list(range(N))
    snake=[]
    for r in range(HUMAN_ROWS):
        row=base[r*HUMAN_COLS:(r+1)*HUMAN_COLS]
        snake.extend(reversed(row) if r%2 else row)
    area_rows=[]
    for r in range(HUMAN_ROWS):
        row=base[r*HUMAN_COLS:(r+1)*HUMAN_COLS]
        area_rows.extend(sorted(row,key=lambda i:-raw[i][1].sum()))
    out=[]
    order_sets=[("serial",base),("snake",snake),("row_area",area_rows)]
    if ROW_PHASE_BASE_PROBE:
        order_sets.extend(row_phase_order_sets(base))
    for label,order in order_sets:
        if len(order)!=N:continue
        rots=[0 for _ in range(N)]
        scs=VISUAL_BASE[:]
        pl=decode_human_slots(order,rots,scs)
        if pl is not None:
            out.append((label,order,rots,scs,pl))
    if MANUAL_STAGGER:
        for ti,template in enumerate(stagger_templates(limit=8)):
            for label,order in order_sets:
                if len(order)!=N:continue
                variants=[0,1,2,5] if ti<3 else [0,1,5]
                for rv in variants:
                    rots=manual_rotation_seed(order,rv)
                    scs=VISUAL_BASE[:]
                    pl=decode_stagger_template(order,rots,scs,template)
                    if pl is not None:
                        out.append((f"stagger{ti}_{label}_r{rv}",order,rots,scs,pl))
    return out

def stagger_slot_beam_seed_layouts():
    if not (STAGGER_SLOT_BEAM_SEED and MANUAL_STAGGER and N==HUMAN_ROWS*HUMAN_COLS):
        return []
    templates=stagger_templates(limit=3)
    if not templates:
        return []
    base=list(range(N))
    areas={i:float(raw[i][1].sum()) for i in base}
    heights={i:int(raw[i][1].shape[0]) for i in base}
    widths={i:int(raw[i][1].shape[1]) for i in base}
    edge=max(EDGE_BLOCK+G,2)
    usable_w=max(1,SW-edge*2)
    usable_h=max(1,SH-edge*2)
    patterns=[
        [0,0,0,0,0],
        [0,180,0,0,0],
        [0,0,180,0,0],
        [0,0,180,0,180],
    ]

    def slot_candidate_items(remaining,row,col):
        cy=(row+0.5)/max(1,HUMAN_ROWS)
        cx=(col+0.5)/max(1,HUMAN_COLS)
        def score(i):
            lower_bonus=1.0+0.22*max(0.0,cy-0.48)
            center_bonus=1.0+0.12*(1.0-abs(cx-0.5)*2.0)
            tall_bonus=heights[i]*0.018*(1.0+0.18*(row in (0,HUMAN_ROWS-1)))
            wide_bonus=widths[i]*0.010*(1.0+0.12*(col in (0,HUMAN_COLS-1)))
            return areas[i]*lower_bonus*center_bonus+tall_bonus+wide_bonus
        ranked=sorted(remaining,key=score,reverse=True)
        flexible=sorted(remaining,key=lambda i:(areas[i],max(heights[i],widths[i])))[:2]
        out=[]
        for idx in ranked[:STAGGER_SLOT_BEAM_SEED_CANDIDATES]+flexible:
            if idx not in out:
                out.append(idx)
            if len(out)>=STAGGER_SLOT_BEAM_SEED_CANDIDATES:
                break
        return out

    out=[]
    node_count=0
    for ti,template in enumerate(templates):
        by={}
        for slot in template.get("slots",[]):
            try:
                by[(int(slot["row"]),int(slot["col"]))]=slot
            except Exception:
                pass
        if len(by)<N:
            continue
        for rv,pattern in enumerate(patterns):
            if node_count>=STAGGER_SLOT_BEAM_SEED_NODE_LIMIT:
                break
            _seed_rots=manual_rotation_seed(base,rv)
            states=[(0.0,[],BASE_OCC.copy(),tuple(base),[],[0 for _ in range(N)],VISUAL_BASE[:])]
            for pos in range(N):
                row=min(HUMAN_ROWS-1,pos//max(1,HUMAN_COLS))
                col=pos%max(1,HUMAN_COLS)
                slot=by.get((row,col),{})
                next_states=[]
                for score_so_far,pl,occ,remaining,order,rots,scs in states:
                    if node_count>=STAGGER_SLOT_BEAM_SEED_NODE_LIMIT:
                        break
                    target_x=edge+(col+0.5)*usable_w/max(1,HUMAN_COLS)
                    target_y=edge+(row+0.5)*usable_h/max(1,HUMAN_ROWS)
                    target_x+=csigned(float(slot.get("dx_mm",0.0))*MANUAL_STAGGER_STRENGTH)
                    target_y+=csigned(float(slot.get("dy_row_mm",0.0))*MANUAL_STAGGER_STRENGTH)
                    for idx in slot_candidate_items(remaining,row,col):
                        if node_count>=STAGGER_SLOT_BEAM_SEED_NODE_LIMIT:
                            break
                        angle=pattern[(col+row*(rv%3))%len(pattern)]
                        if angle not in ANG:
                            angle=_seed_rots[idx]
                        scale=VISUAL_BASE[idx]
                        m=make(idx,angle,scale)
                        x0=min(max(0,target_x-m.shape[1]/2),max(0,SW-m.shape[1]))
                        y0=min(max(0,target_y-m.shape[0]/2),max(0,SH-m.shape[0]))
                        p=place_guided(occ,m,x0,y0,row_strength=1.35)
                        if p is None:
                            p=place(occ,m)
                        node_count+=1
                        if p is None:
                            continue
                        occ2=occ.copy()
                        stamp(occ2,p[0],p[1],m)
                        pl2=pl+[(idx,p[0],p[1],angle,scale)]
                        if orientation_hard_reject(pl2):
                            continue
                        rots2=rots[:]
                        scs2=scs[:]
                        rots2[idx]=angle
                        scs2[idx]=scale
                        remaining2=tuple(v for v in remaining if v!=idx)
                        order2=order+[idx]
                        score2=score_so_far+layout_quality(pl2)+ink(pl2)*2.5-row_column_imbalance(pl2)*0.35
                        next_states.append((score2,pl2,occ2,remaining2,order2,rots2,scs2))
                states=sorted(next_states,key=lambda entry:entry[0],reverse=True)[:STAGGER_SLOT_BEAM_SEED_WIDTH]
                if not states:
                    break
            for score,pl,_,remaining,order,rots,scs in states:
                if len(pl)==N and not remaining and not orientation_hard_reject(pl):
                    out.append((f"stagger_slot_beam_t{ti}_r{rv}",order,rots,scs,pl))
                    if RECOVERY_DEBUG:
                        print(f"stagger_slot_beam_seed label=stagger_slot_beam_t{ti}_r{rv} quality={layout_quality(pl):.4f} ink={ink(pl)*100:.1f}% nodes={node_count}", file=sys.stderr)
            if len(out)>=4:
                break
        if len(out)>=4 or node_count>=STAGGER_SLOT_BEAM_SEED_NODE_LIMIT:
            break
    return out

best=-1e9;bestInk=0;bestpl=None;t0=time.time();random.seed(SEED)
if not POLISH_BASE_JSON:
    baseline_order=sorted(range(N),key=lambda i:-raw[i][1].shape[0])
    baseline_rots=[0 for _ in range(N)]
    baseline_scs=VISUAL_BASE[:]
    baseline_pl=decode_initial(baseline_order,baseline_rots,baseline_scs)
    if baseline_pl is not None:
        best=layout_quality(baseline_pl);bestInk=ink(baseline_pl);bestpl=baseline_pl
        if RECOVERY_DEBUG:
            print(f"baseline_seed quality={best:.4f} ink={bestInk*100:.1f}% placed={len(baseline_pl)}/{N}", file=sys.stderr)
    for label,order,rots,scs,pl in human_seed_layouts():
        q=layout_quality(pl);a=ink(pl)
        if q>best:best=q;bestInk=a;bestpl=pl
        if RECOVERY_DEBUG:
            print(f"human_imitation_seed label={label} quality={q:.4f} ink={a*100:.1f}% placed={len(pl)}/{N}", file=sys.stderr)
    for label,order,rots,scs,pl in stagger_slot_beam_seed_layouts():
        q=layout_quality(pl);a=ink(pl)
        if q>best:best=q;bestInk=a;bestpl=pl
        if RECOVERY_DEBUG:
            print(f"stagger_slot_beam_seed_selected label={label} quality={q:.4f} ink={a*100:.1f}% placed={len(pl)}/{N}", file=sys.stderr)
    while time.time()-t0<SECS:
        if HUMAN_IMITATION and random.random()<0.08:
            order=list(range(N))
        else:
            order=sorted(range(N),key=lambda i:-raw[i][1].shape[0])
        for _ in range(random.randint(0,8)):a,b=random.randrange(N),random.randrange(N);order[a],order[b]=order[b],order[a]
        rots=manual_rotation_seed(order,random.randrange(6)) if (MANUAL_STAGGER and random.random()<0.22) else [0 for _ in range(N)]
        scs=VISUAL_BASE[:]
        templates=stagger_templates(limit=10)
        if MANUAL_STAGGER and templates and random.random()<0.14:
            pl=decode_stagger_template(order,rots,scs,random.choice(templates))
            if pl is None:pl=decode_initial(order,rots,scs)
        elif HUMAN_IMITATION and random.random()<0.06:
            pl=decode_human_slots(order,rots,scs)
            if pl is None:pl=decode_initial(order,rots,scs)
        else:
            pl=decode_initial(order,rots,scs)
        if pl is None:continue
        cur=layout_quality(pl);curInk=ink(pl);T=0.05
        if cur>best:best=cur;bestInk=curInk;bestpl=pl
        for _ in range(80):
            if time.time()-t0>=SECS:break
            nO,nR,nS=order[:],rots[:],scs[:];rr=random.random()
            if rr<0.4:a,b=random.randrange(N),random.randrange(N);nO[a],nO[b]=nO[b],nO[a]
            elif rr<0.7:a=random.randrange(N);nR[a]=random.choice(ANG)
            else:a=random.randrange(N);nS[a]=random.choice(candidate_scales(a))
            if MANUAL_STAGGER and templates and random.random()<0.10:
                p2=decode_stagger_template(nO,nR,nS,random.choice(templates))
            elif HUMAN_IMITATION and random.random()<0.06:
                p2=decode_human_slots(nO,nR,nS)
            else:
                p2=decode(nO,nR,nS)
            if p2 is None:continue
            e=layout_quality(p2);ei=ink(p2)
            if e>=cur or random.random()<math.exp((e-cur)/max(0.001,T)):order,rots,scs,cur,curInk=nO,nR,nS,e,ei
            if e>best:best=e;bestInk=ei;bestpl=p2
            T*=0.97
# 重力压实:逐张拿出重塞到最贴合处,反复几轮,挤掉零散白缝
def compact(pl, rounds=4):
    pl=pl[:]
    for _ in range(rounds):
        order=sorted(range(len(pl)), key=lambda k:(pl[k][2],pl[k][1]))
        for k in order:
            occ=BASE_OCC.copy()
            for j in range(len(pl)):
                if j==k: continue
                ii,xx,yy,rr,ss=pl[j]; mm=make(ii,rr,ss); occ[yy:yy+mm.shape[0],xx:xx+mm.shape[1]]|=mm
            i,x,y,r,s=pl[k]; m=make(i,r,s); p=place(occ,m)
            if p: pl[k]=(i,p[0],p[1],r,s)
    return pl
# 逐张填缝放大:每张就地长进周围空当(各自大小,最大化填充)
def growfill(pl, rounds=8):
    pl=pl[:]
    for _ in range(rounds):
        order=sorted(range(len(pl)), key=lambda k:-(make(pl[k][0],pl[k][3],pl[k][4]).size))
        for k in range(len(pl)):
            occ=BASE_OCC.copy()
            for j in range(len(pl)):
                if j==k: continue
                ii,xx,yy,rr,ss=pl[j]; mm=make(ii,rr,ss); occ[yy:yy+mm.shape[0],xx:xx+mm.shape[1]]|=mm
            i,x,y,r,s=pl[k]; done=False
            grow_scales=sorted(set(clamp_scale(i,s*f) for f in [1.30,1.22,1.15,1.09,1.04]), reverse=True)
            grow_angles=local_angle_candidates(r,broad=False)[:4 if MANUAL_STAGGER else 1]
            for rr in grow_angles:
                for gs in grow_scales:
                    if gs <= s + 0.003 and rr==r:
                        continue
                    m=make(i,rr,gs); h,w=m.shape
                    if h>SH or w>SW: continue
                    for dy in [0,-2,2,-5,5,-9,9,-14,14]:
                        for dx in [0,-2,2,-5,5,-9,9,-14,14]:
                            nx=min(max(0,x+dx),SW-w); ny=min(max(0,y+dy),SH-h)
                            if not occ[ny:ny+h,nx:nx+w][m].any():
                                trial=pl[:]
                                trial[k]=(i,nx,ny,rr,gs)
                                if not orientation_hard_reject(trial):
                                    pl=trial; done=True; break
                        if done: break
                    if done: break
                if done: break
    return pl

def sparse_targets(pl, limit=10):
    g=gap_occupancy(pl)
    targets=[]
    for ty in range(8):
        for tx in range(10):
            x0=SW*tx/10;y0=SH*ty/8;x1=SW*(tx+1)/10;y1=SH*(ty+1)/8
            x0i=max(0,int(x0));y0i=max(0,int(y0));x1i=min(SW,int(x1));y1i=min(SH,int(y1))
            allowed=(~BASE_OCC[y0i:y1i,x0i:x1i])
            denom=int(allowed.sum())
            if denom<20:
                continue
            fill=float((g[y0i:y1i,x0i:x1i]&allowed).sum())/max(1,denom)
            blank=1.0-fill
            cy=(ty+0.5)/8;cx=(tx+0.5)/10
            center_weight=1.0+0.35*(1.0-abs(cx-0.5)*2.0)
            lower_weight=1.0+0.55*max(0.0,cy-0.52)
            score=blank*center_weight*lower_weight
            if blank>0.46:
                targets.append((score,blank,(x0+x1)/2,(y0+y1)/2,tx,ty))
    targets.sort(reverse=True)
    return targets[:limit]

def visual_audit_like(pl):
    g=gap_occupancy(pl)
    rows=10;cols=8
    tile=[]
    for row in range(rows):
        y0=row*SH//rows;y1=(row+1)*SH//rows
        for col in range(cols):
            x0=col*SW//cols;x1=(col+1)*SW//cols
            tile.append(float(g[y0:y1,x0:x1].mean()))
    sparse=[v<0.28 for v in tile]
    seen=[False]*(rows*cols)
    largest=0
    for index,is_sparse in enumerate(sparse):
        if not is_sparse or seen[index]:
            continue
        queue=[index];seen[index]=True;count=0
        while queue:
            current=queue.pop();count+=1
            row=current//cols;col=current%cols
            for nr,nc in ((row-1,col),(row+1,col),(row,col-1),(row,col+1)):
                if 0<=nr<rows and 0<=nc<cols:
                    ni=nr*cols+nc
                    if sparse[ni] and not seen[ni]:
                        seen[ni]=True;queue.append(ni)
        largest=max(largest,count)
    def blank(x0,x1,y0,y1):
        x0=max(0,int(x0));x1=min(SW,int(x1));y0=max(0,int(y0));y1=min(SH,int(y1))
        if x1<=x0 or y1<=y0:
            return 1.0
        return 1.0-float(g[y0:y1,x0:x1].mean())
    center_blank=blank(SW/4,SW*3/4,SH/4,SH*3/4)
    lower_blank=blank(SW/8,SW*7/8,SH*3/4,SH)
    row_fills=[sum(tile[row*cols:(row+1)*cols])/cols for row in range(rows)]
    col_fills=[sum(tile[row*cols+col] for row in range(rows))/rows for col in range(cols)]
    row_imbalance=(max(row_fills) if row_fills else 0.0)-(min(row_fills) if row_fills else 0.0)
    col_imbalance=(max(col_fills) if col_fills else 0.0)-(min(col_fills) if col_fills else 0.0)
    alpha=ink(pl)
    grid=float(g.sum())/max(1,SW*SH)
    ys,xs=np.where(g & (~BASE_OCC))
    layout_bbox=0.0
    if len(xs)>0 and len(ys)>0:
        layout_bbox=((xs.max()-xs.min()+1)*(ys.max()-ys.min()+1))/max(1,SW*SH)
    cv=size_cv(pl)
    largest_area=largest/max(1,rows*cols)
    penalty=0
    penalty+=int(max(0,0.78-grid)*300)
    penalty+=int(max(0,0.58-alpha)*120)
    penalty+=int(max(0,largest_area-0.06)*360)
    penalty+=int(max(0,center_blank-0.34)*95)
    penalty+=int(max(0,lower_blank-0.36)*90)
    penalty+=int(row_imbalance*50)
    penalty+=int(col_imbalance*45)
    penalty+=int(max(0,cv-0.09)*150)
    score=max(0,min(100,100-penalty))
    selection=score*500+alpha*260000+grid*80000+layout_bbox*1000-row_imbalance*120-col_imbalance*90-cv*120
    return {
        "score":score,
        "selection":selection,
        "grid":grid,
        "alpha":alpha,
        "layout_bbox":layout_bbox,
        "large_blank":largest_area,
        "center_blank":center_blank,
        "lower_blank":lower_blank,
        "row_imbalance":row_imbalance,
        "column_imbalance":col_imbalance,
        "size_cv":cv,
        "row_fills":row_fills,
        "column_fills":col_fills,
        "tile_fills":tile,
    }

def build_occ_except_positions(pl, skip_positions):
    skip_positions=set(skip_positions or [])
    occ=BASE_OCC.copy()
    for pos,(i,x,y,r,s) in enumerate(pl):
        if pos in skip_positions:
            continue
        stamp(occ,x,y,make(i,r,s,gap=True))
    return occ

def layout_overlap_pairs(pl):
    occ=np.zeros((SH,SW),bool)
    owners=np.full((SH,SW),-1,np.int16)
    pairs={}
    overlap=0
    for pos,(i,x,y,r,s) in enumerate(pl):
        m=make(i,r,s,gap=True)
        h,w=m.shape
        if x<0 or y<0 or x+w>SW or y+h>SH:
            pairs[(-1,pos)]=1
            overlap+=1
            continue
        region=occ[y:y+h,x:x+w]
        owner_region=owners[y:y+h,x:x+w]
        if region.shape!=m.shape or owner_region.shape!=m.shape:
            pairs[(-1,pos)]=1
            overlap+=1
            continue
        hit=region&m
        if hit.any():
            overlap+=int(hit.sum())
            for previous in np.unique(owner_region[hit]):
                if previous>=0:
                    pair=tuple(sorted((int(previous),pos)))
                    pairs[pair]=pairs.get(pair,0)+int(((owner_region==previous)&m).sum())
        region[m]=True
        owner_region[m]=pos
    return pairs,overlap

def layout_overlap_cells(pl):
    _,overlap=layout_overlap_pairs(pl)
    return overlap

def local_cluster_repack_targets(pl, audit, limit=2):
    rows=10;cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    targets=[]
    for row in range(rows):
        for col in range(cols):
            fill=audit["tile_fills"][row*cols+col]
            sparse=max(0.0,0.28-fill)*4.0
            row_deficit=max(0.0,row_mean-audit["row_fills"][row])
            col_deficit=max(0.0,col_mean-audit["column_fills"][col])
            score=sparse+row_deficit*1.6+col_deficit*1.2
            if score<=0.035:
                continue
            cx=(col+0.5)*SW/cols
            cy=(row+0.5)*SH/rows
            targets.append((score,cx,cy,row,col))
    targets.sort(reverse=True)
    return targets[:limit]

def local_cluster_repack(pl, rounds=1):
    if not (LOCAL_CLUSTER_REPACK and MANUAL_STAGGER) or not pl:
        return pl
    pl=pl[:]
    for _ in range(rounds):
        base_audit=visual_audit_like(pl)
        base_quality=layout_quality(pl)
        base_alpha=ink(pl)
        base_stats=orientation_stats(pl)
        row_mean=sum(base_audit["row_fills"])/max(1,len(base_audit["row_fills"]))
        col_mean=sum(base_audit["column_fills"])/max(1,len(base_audit["column_fills"]))
        weight=np.zeros((SH,SW),np.float32)
        for row,value in enumerate(base_audit["row_fills"]):
            weight[row*SH//10:(row+1)*SH//10,:]+=max(0.0,row_mean-value)*1.6
            weight[row*SH//10:(row+1)*SH//10,:]-=max(0.0,value-row_mean)*0.4
        for col,value in enumerate(base_audit["column_fills"]):
            weight[:,col*SW//8:(col+1)*SW//8]+=max(0.0,col_mean-value)*1.2
            weight[:,col*SW//8:(col+1)*SW//8]-=max(0.0,value-col_mean)*0.3
        for _,_,_,row,col in local_cluster_repack_targets(pl,base_audit,limit=LOCAL_CLUSTER_REPACK_TARGETS):
            weight[row*SH//10:(row+1)*SH//10,col*SW//8:(col+1)*SW//8]+=0.45

        masks=[make(i,r,s,gap=True) for i,_,_,r,s in pl]
        areas=[max(1,int(m.sum())) for m in masks]
        positions=[(x,y) for _,x,y,_,_ in pl]

        def position_score(pos,x,y):
            m=masks[pos]
            return float(weight[y:y+m.shape[0],x:x+m.shape[1]][m].sum())/areas[pos] - 0.0008*(abs(x-positions[pos][0])+abs(y-positions[pos][1]))

        def feasible_positions(pos,fixed,region,limit):
            m=masks[pos];h,w=m.shape
            x0,y0,x1,y1=region
            x0=max(0,min(SW-w,int(x0)));x1=max(0,min(SW-w,int(x1)))
            y0=max(0,min(SH-h,int(y0)));y1=max(0,min(SH-h,int(y1)))
            candidates={positions[pos]}
            for yy in range(y0,y1+1,2):
                for xx in range(x0,x1+1,2):
                    candidates.add((xx,yy))
            scored=[]
            for xx,yy in candidates:
                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                    continue
                region_occ=fixed[yy:yy+h,xx:xx+w]
                if region_occ.shape==m.shape and not (region_occ&m).any():
                    scored.append((position_score(pos,xx,yy),xx,yy))
            scored.sort(reverse=True)
            top=scored[:limit]
            current=[entry for entry in scored if (entry[1],entry[2])==positions[pos]]
            for entry in current:
                if entry not in top:
                    top.append(entry)
            return [(xx,yy) for _,xx,yy in top]

        best_trial=None
        best_gain=0.0
        for target_score,cx,cy,_,_ in local_cluster_repack_targets(pl,base_audit,limit=LOCAL_CLUSTER_REPACK_TARGETS):
            center_dist=[]
            for pos,(i,x,y,r,s) in enumerate(pl):
                m=masks[pos]
                px=x+m.shape[1]/2;py=y+m.shape[0]/2
                center_dist.append((abs(px-cx)+abs(py-cy),pos))
            near=[pos for _,pos in sorted(center_dist)[:LOCAL_CLUSTER_REPACK_NEAR]]
            region=(
                cx-SW*0.28,
                cy-SH*0.23,
                cx+SW*0.28,
                cy+SH*0.23,
            )
            for cluster_size in (3,):
                if len(near)<cluster_size:
                    continue
                for subset in itertools.combinations(near,cluster_size):
                    fixed=build_occ_except_positions(pl,subset)
                    candidate_positions={}
                    valid=True
                    for pos in subset:
                        opts=feasible_positions(pos,fixed,region,LOCAL_CLUSTER_REPACK_POSITIONS if cluster_size==3 else max(16,LOCAL_CLUSTER_REPACK_POSITIONS//2))
                        if not opts:
                            valid=False
                            break
                        candidate_positions[pos]=opts
                    if not valid:
                        continue
                    order=sorted(subset,key=lambda pos:len(candidate_positions[pos]))
                    occ=fixed.copy()
                    current={}
                    nodes=0

                    def rebuild_occ():
                        occ[:]=fixed
                        for pp,(xx,yy) in current.items():
                            stamp(occ,xx,yy,masks[pp])

                    def dfs(depth):
                        nonlocal nodes,best_trial,best_gain,occ
                        nodes+=1
                        if nodes>LOCAL_CLUSTER_REPACK_NODE_LIMIT:
                            return
                        if depth==len(order):
                            trial=pl[:]
                            moved=0
                            for pp,(xx,yy) in current.items():
                                i,_,_,r,s=trial[pp]
                                trial[pp]=(i,xx,yy,r,s)
                                moved+=abs(xx-positions[pp][0])+abs(yy-positions[pp][1])
                            if moved<4:
                                return
                            trial_audit=visual_audit_like(trial)
                            trial_stats=orientation_stats(trial)
                            if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                return
                            if ink(trial)<base_alpha-0.0005:
                                return
                            if trial_audit["large_blank"]>base_audit["large_blank"]+1e-9:
                                return
                            if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.003:
                                return
                            if trial_audit["center_blank"]>base_audit["center_blank"]+0.025:
                                return
                            if trial_audit["score"]<base_audit["score"]+3:
                                return
                            if trial_audit["selection"]<base_audit["selection"]+500:
                                return
                            trial_quality=layout_quality(trial)
                            if trial_quality<base_quality-0.090:
                                return
                            gain=(trial_audit["selection"]-base_audit["selection"]) + (base_audit["row_imbalance"]-trial_audit["row_imbalance"])*2500 + (base_audit["column_imbalance"]-trial_audit["column_imbalance"])*1800 - max(0.0,trial_audit["center_blank"]-base_audit["center_blank"])*400
                            if gain>best_gain:
                                best_gain=gain
                                best_trial=trial
                            return
                        pos=order[depth]
                        m=masks[pos];h,w=m.shape
                        for xx,yy in candidate_positions[pos]:
                            region_occ=occ[yy:yy+h,xx:xx+w]
                            if region_occ.shape!=m.shape or (region_occ&m).any():
                                continue
                            current[pos]=(xx,yy)
                            stamp(occ,xx,yy,m)
                            dfs(depth+1)
                            current.pop(pos,None)
                            rebuild_occ()
                    dfs(0)

        if best_trial is None:
            break
        after=visual_audit_like(best_trial)
        if RECOVERY_DEBUG:
            print(f"local_cluster_repack visual={base_audit['score']}->{after['score']} rowImbalance={base_audit['row_imbalance']:.3f}->{after['row_imbalance']:.3f} colImbalance={base_audit['column_imbalance']:.3f}->{after['column_imbalance']:.3f} centerBlank={base_audit['center_blank']:.3f}->{after['center_blank']:.3f} lowerBlank={base_audit['lower_blank']:.3f}->{after['lower_blank']:.3f}", file=sys.stderr)
        pl=best_trial
    return pl

def material_alpha_topup_seed_allowed():
    raw_text=str(MATERIAL_ALPHA_TOPUP_SEEDS or "").strip().lower()
    if raw_text in ("", "*", "all"):
        return True
    allowed=set()
    for token in raw_text.replace(";",",").split(","):
        token=token.strip()
        if not token:
            continue
        try:
            allowed.add(int(token))
        except Exception:
            pass
    return SEED in allowed

def material_alpha_topup_alpha(pl):
    return float(content_occupancy(pl).sum())/max(1,SW*SH)

def material_alpha_topup(pl, rounds=1):
    if not (MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed():
        return pl
    if len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    if base_alpha>=MATERIAL_ALPHA_TOPUP_TARGET-1e-6:
        return pl
    if base_alpha<MATERIAL_ALPHA_TOPUP_TARGET-MATERIAL_ALPHA_TOPUP_MAX_DEFICIT:
        return pl

    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    accepted=0
    factors=[1.003,1.005,1.007,1.009,1.012,1.015,1.018,1.022,1.026]
    offsets=[0]
    for step in range(1,MATERIAL_ALPHA_TOPUP_MAX_NUDGE+1):
        offsets.extend([-step,step])

    for _ in range(max(1,rounds)):
        while accepted<MATERIAL_ALPHA_TOPUP_MAX_MOVES and material_alpha_topup_alpha(current)<MATERIAL_ALPHA_TOPUP_TARGET-1e-6:
            cur_alpha=material_alpha_topup_alpha(current)
            best_move=None
            for pos,(i,x,y,r,s) in enumerate(current):
                old=make(i,r,s,gap=True)
                cx=x+old.shape[1]/2
                cy=y+old.shape[0]/2
                fixed=build_occ_except_positions(current,{pos})
                for factor in factors:
                    ns=round(clamp_scale(i,s*factor),4)
                    if ns<=s+0.0004:
                        continue
                    m=make(i,r,ns,gap=True)
                    h,w=m.shape
                    if h>SH or w>SW:
                        continue
                    base_x=int(round(cx-w/2))
                    base_y=int(round(cy-h/2))
                    for dy in offsets:
                        for dx in offsets:
                            nx=min(max(0,base_x+dx),SW-w)
                            ny=min(max(0,base_y+dy),SH-h)
                            region=fixed[ny:ny+h,nx:nx+w]
                            if region.shape!=m.shape or region[m].any():
                                continue
                            trial=current[:]
                            trial[pos]=(i,nx,ny,r,ns)
                            trial_stats=orientation_stats(trial)
                            if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                continue
                            trial_alpha=material_alpha_topup_alpha(trial)
                            if trial_alpha<=cur_alpha+0.00002:
                                continue
                            trial_audit=visual_audit_like(trial)
                            if trial_audit["score"]<base_audit["score"]-1:
                                continue
                            if trial_audit["large_blank"]>base_audit["large_blank"]+0.012:
                                continue
                            if trial_audit["center_blank"]>base_audit["center_blank"]+0.025:
                                continue
                            if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.025:
                                continue
                            if trial_audit["size_cv"]>base_cv+0.006:
                                continue
                            trial_quality=layout_quality(trial)
                            if trial_quality<base_quality-0.055:
                                continue
                            move=abs(nx-x)+abs(ny-y)
                            gain=trial_alpha-cur_alpha
                            score=gain*100000.0 - move*0.12
                            score-=max(0.0,trial_audit["size_cv"]-base_cv)*300.0
                            score+=(base_audit["lower_blank"]-trial_audit["lower_blank"])*220.0
                            score+=(base_audit["center_blank"]-trial_audit["center_blank"])*120.0
                            score+=(base_audit["column_imbalance"]-trial_audit["column_imbalance"])*28.0
                            if best_move is None or score>best_move[0]:
                                best_move=(score,pos,nx,ny,ns,trial_alpha,trial_audit)
            if best_move is None:
                break
            _,pos,nx,ny,ns,trial_alpha,trial_audit=best_move
            i,x,y,r,s=current[pos]
            current[pos]=(i,nx,ny,r,ns)
            accepted+=1
            if RECOVERY_DEBUG:
                print(f"material_alpha_topup item={raw[i][0]} scale={s:.4f}->{ns:.4f} alpha={trial_alpha*100:.3f}% visual={trial_audit['score']}", file=sys.stderr)
        if ink(current)>=MATERIAL_ALPHA_TOPUP_TARGET-1e-6:
            break

    final_alpha=material_alpha_topup_alpha(current)
    target_reached=final_alpha>=MATERIAL_ALPHA_TOPUP_TARGET-1e-6
    partial_threshold=max(MATERIAL_ALPHA_TOPUP_MIN_ACCEPT,base_alpha+MATERIAL_ALPHA_TOPUP_MIN_GAIN)
    partial_reached=final_alpha>=partial_threshold-1e-6
    if accepted>0 and (target_reached or partial_reached):
        final_audit=visual_audit_like(current)
        final_stats=orientation_stats(current)
        if final_audit["score"]>=base_audit["score"]-1 and final_stats["readable"]>=base_stats["readable"] and final_stats["upside"]<=base_stats["upside"] and final_stats["sideways"]<=base_stats["sideways"] and final_stats["hard"]<=base_stats["hard"]:
            global MATERIAL_ALPHA_TOPUP_APPLIED, MATERIAL_ALPHA_TOPUP_PARTIAL, MATERIAL_ALPHA_TOPUP_MOVES
            MATERIAL_ALPHA_TOPUP_APPLIED=True
            MATERIAL_ALPHA_TOPUP_PARTIAL=not target_reached
            MATERIAL_ALPHA_TOPUP_MOVES=accepted
            if RECOVERY_DEBUG:
                partial_text=" partial=1" if MATERIAL_ALPHA_TOPUP_PARTIAL else ""
                print(f"material_alpha_topup accepted moves={accepted} alpha={base_alpha*100:.3f}->{final_alpha*100:.3f}% visual={base_audit['score']}->{final_audit['score']}{partial_text}", file=sys.stderr)
            return current
    return pl

def mask_overlap_blockers(pl, grow_pos, nx, ny, m):
    h,w=m.shape
    if nx<0 or ny<0 or nx+w>SW or ny+h>SH:
        return None
    base_region=BASE_OCC[ny:ny+h,nx:nx+w]
    if base_region.shape!=m.shape or (base_region&m).any():
        return None
    blockers=[]
    for pos,(i,x,y,r,s) in enumerate(pl):
        if pos==grow_pos:
            continue
        om=make(i,r,s,gap=True)
        oh,ow=om.shape
        x0=max(nx,x);y0=max(ny,y)
        x1=min(nx+w,x+ow);y1=min(ny+h,y+oh)
        if x1<=x0 or y1<=y0:
            continue
        if (m[y0-ny:y1-ny,x0-nx:x1-nx] & om[y0-y:y1-y,x0-x:x1-x]).any():
            blockers.append(pos)
            if len(blockers)>MULTI_PIECE_TOPUP_MAX_BLOCKERS:
                return None
    return blockers

def multi_piece_relocation_options(pl, pos, fixed, limit):
    i,x,y,r,s=pl[pos]
    m=make(i,r,s,gap=True)
    h,w=m.shape
    cx=x+w/2
    cy=y+h/2
    candidates={(x,y)}
    radii=[0,3,6,10,14,20,28,MULTI_PIECE_TOPUP_RELOCATE_RADIUS]
    for radius in radii:
        radius=int(radius)
        step=max(1,radius//4)
        for dy in range(-radius,radius+1,step):
            for dx in range(-radius,radius+1,step):
                if radius and abs(dx)!=radius and abs(dy)!=radius:
                    continue
                candidates.add((min(max(0,x+dx),SW-w),min(max(0,y+dy),SH-h)))
    scored=[]
    wall=dil(fixed,1)&(~fixed)
    for xx,yy in candidates:
        region=fixed[yy:yy+h,xx:xx+w]
        if region.shape!=m.shape or (region&m).any():
            continue
        sub=wall[yy:yy+h,xx:xx+w]
        contact=float((sub&m).sum()) if sub.shape==m.shape else 0.0
        dist=abs((xx+w/2)-cx)+abs((yy+h/2)-cy)
        scored.append((contact*0.08-dist,xx,yy))
    scored.sort(reverse=True)
    return [(xx,yy) for _,xx,yy in scored[:limit]]

def multi_piece_material_topup(pl, rounds=1):
    if not (MULTI_PIECE_TOPUP and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed():
        return pl
    if len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    if base_alpha>=MULTI_PIECE_TOPUP_TARGET-1e-6:
        return pl
    if base_alpha<MULTI_PIECE_TOPUP_TARGET-MATERIAL_ALPHA_TOPUP_MAX_DEFICIT:
        return pl
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    accepted=0
    factors=[1.003,1.005,1.007,1.009,1.012,1.015]
    offsets=[0]
    for step in range(1,MULTI_PIECE_TOPUP_MAX_NUDGE+1):
        offsets.extend([-step,step])

    for _ in range(max(1,rounds)):
        while accepted<MULTI_PIECE_TOPUP_MAX_MOVES and material_alpha_topup_alpha(current)<MULTI_PIECE_TOPUP_TARGET-1e-6:
            cur_alpha=material_alpha_topup_alpha(current)
            best_move=None
            node_count=0
            target_order=sorted(
                range(len(current)),
                key=lambda pp:(SCALE_HI[current[pp][0]]-current[pp][4])*max(1,int(make(current[pp][0],current[pp][3],current[pp][4],gap=False).sum())),
                reverse=True
            )[:MULTI_PIECE_TOPUP_TARGETS]
            for pos in target_order:
                i,x,y,r,s=current[pos]
                old=make(i,r,s,gap=True)
                cx=x+old.shape[1]/2
                cy=y+old.shape[0]/2
                for factor in factors:
                    ns=round(clamp_scale(i,s*factor),4)
                    if ns<=s+0.0004:
                        continue
                    m=make(i,r,ns,gap=True)
                    h,w=m.shape
                    if h>SH or w>SW:
                        continue
                    base_x=int(round(cx-w/2))
                    base_y=int(round(cy-h/2))
                    for dy in offsets:
                        for dx in offsets:
                            nx=min(max(0,base_x+dx),SW-w)
                            ny=min(max(0,base_y+dy),SH-h)
                            blockers=mask_overlap_blockers(current,pos,nx,ny,m)
                            if blockers is None or not blockers:
                                continue
                            fixed=build_occ_except_positions(current,set([pos]+blockers))
                            region=fixed[ny:ny+h,nx:nx+w]
                            if region.shape!=m.shape or (region&m).any():
                                continue
                            fixed_with_grow=fixed.copy()
                            stamp(fixed_with_grow,nx,ny,m)
                            options={}
                            valid=True
                            for blocker in blockers:
                                opts=multi_piece_relocation_options(current,blocker,fixed_with_grow,MULTI_PIECE_TOPUP_OPTIONS)
                                if not opts:
                                    valid=False
                                    break
                                options[blocker]=opts
                            if not valid:
                                continue
                            order=sorted(blockers,key=lambda pp:len(options[pp]))
                            occ=fixed_with_grow.copy()
                            placed={}
                            best_trial_for_move=None
                            best_trial_score=-1e18

                            def rebuild_occ():
                                occ[:]=fixed_with_grow
                                for pp,(xx,yy) in placed.items():
                                    bi,_,_,br,bs=current[pp]
                                    stamp(occ,xx,yy,make(bi,br,bs,gap=True))

                            def dfs(depth):
                                nonlocal best_trial_for_move,best_trial_score,occ,node_count
                                node_count+=1
                                if node_count> MULTI_PIECE_TOPUP_NODE_LIMIT:
                                    return
                                if depth==len(order):
                                    trial=current[:]
                                    trial[pos]=(i,nx,ny,r,ns)
                                    moved=abs(nx-x)+abs(ny-y)
                                    for pp,(xx,yy) in placed.items():
                                        bi,bx,by,br,bs=trial[pp]
                                        trial[pp]=(bi,xx,yy,br,bs)
                                        moved+=abs(xx-bx)+abs(yy-by)
                                    trial_stats=orientation_stats(trial)
                                    if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                        return
                                    trial_alpha=material_alpha_topup_alpha(trial)
                                    if trial_alpha<=cur_alpha+0.00002:
                                        return
                                    trial_audit=visual_audit_like(trial)
                                    if trial_audit["score"]<base_audit["score"]-1:
                                        return
                                    if trial_audit["large_blank"]>base_audit["large_blank"]+0.014:
                                        return
                                    if trial_audit["center_blank"]>base_audit["center_blank"]+0.026:
                                        return
                                    if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.026:
                                        return
                                    if trial_audit["size_cv"]>base_cv+0.008:
                                        return
                                    trial_quality=layout_quality(trial)
                                    if trial_quality<base_quality-0.070:
                                        return
                                    score=(trial_alpha-cur_alpha)*120000.0 - moved*0.055
                                    score+=(base_audit["lower_blank"]-trial_audit["lower_blank"])*220.0
                                    score+=(base_audit["center_blank"]-trial_audit["center_blank"])*120.0
                                    score+=(trial_audit["selection"]-base_audit["selection"])*0.010
                                    if score>best_trial_score:
                                        best_trial_score=score
                                        best_trial_for_move=(trial,trial_alpha,trial_audit,moved,len(blockers))
                                    return
                                pp=order[depth]
                                bi,_,_,br,bs=current[pp]
                                bm=make(bi,br,bs,gap=True)
                                bh,bw=bm.shape
                                for xx,yy in options[pp]:
                                    region=occ[yy:yy+bh,xx:xx+bw]
                                    if region.shape!=bm.shape or (region&bm).any():
                                        continue
                                    placed[pp]=(xx,yy)
                                    stamp(occ,xx,yy,bm)
                                    dfs(depth+1)
                                    placed.pop(pp,None)
                                    rebuild_occ()

                            dfs(0)
                            if node_count> MULTI_PIECE_TOPUP_NODE_LIMIT:
                                break
                            if best_trial_for_move is None:
                                continue
                            trial,trial_alpha,trial_audit,moved,blocker_count=best_trial_for_move
                            gain=trial_alpha-cur_alpha
                            score=gain*100000.0 - moved*0.040 - blocker_count*2.0
                            score+=(base_audit["lower_blank"]-trial_audit["lower_blank"])*160.0
                            score+=(base_audit["center_blank"]-trial_audit["center_blank"])*100.0
                            if best_move is None or score>best_move[0]:
                                best_move=(score,pos,ns,trial,trial_alpha,trial_audit,moved,blocker_count)
                        if node_count> MULTI_PIECE_TOPUP_NODE_LIMIT:
                            break
                    if node_count> MULTI_PIECE_TOPUP_NODE_LIMIT:
                        break
                if node_count> MULTI_PIECE_TOPUP_NODE_LIMIT:
                    break
            if best_move is None:
                break
            _,pos,ns,trial,trial_alpha,trial_audit,moved,blocker_count=best_move
            old_scale=current[pos][4]
            current=trial
            accepted+=1
            if RECOVERY_DEBUG:
                print(f"multi_piece_topup item={raw[current[pos][0]][0]} scale={old_scale:.4f}->{ns:.4f} blockers={blocker_count} move={moved} alpha={trial_alpha*100:.3f}% visual={trial_audit['score']}", file=sys.stderr)
        if material_alpha_topup_alpha(current)>=MULTI_PIECE_TOPUP_TARGET-1e-6:
            break

    final_alpha=material_alpha_topup_alpha(current)
    accept_threshold=max(MULTI_PIECE_TOPUP_MIN_ACCEPT,base_alpha+MULTI_PIECE_TOPUP_MIN_GAIN)
    if accepted>0 and final_alpha>=accept_threshold-1e-6:
        final_audit=visual_audit_like(current)
        final_stats=orientation_stats(current)
        if final_audit["score"]>=base_audit["score"]-1 and final_stats["readable"]>=base_stats["readable"] and final_stats["upside"]<=base_stats["upside"] and final_stats["sideways"]<=base_stats["sideways"] and final_stats["hard"]<=base_stats["hard"]:
            global MULTI_PIECE_TOPUP_APPLIED, MULTI_PIECE_TOPUP_MOVES
            MULTI_PIECE_TOPUP_APPLIED=True
            MULTI_PIECE_TOPUP_MOVES=accepted
            if RECOVERY_DEBUG:
                print(f"multi_piece_topup accepted moves={accepted} alpha={base_alpha*100:.3f}->{final_alpha*100:.3f}% visual={base_audit['score']}->{final_audit['score']}", file=sys.stderr)
            return current
    return pl

def local_adapter_target_tiles():
    tiles=[]
    for part in re.split(r"[,;|]", str(LOCAL_ADAPTER_TARGET_TILES or "")):
        nums=[int(v) for v in re.findall(r"-?\d+", part)]
        if len(nums)>=2:
            row=max(0,min(9,nums[0]))
            col=max(0,min(7,nums[1]))
            tiles.append((row,col))
    return tiles or [(5,4)]

def local_adapter_audit_void_tiles(pl, audit):
    if not (LOCAL_ADAPTER_V2 and LOCAL_ADAPTER_TARGET_MODE in ("audit_voids","hybrid")):
        return []
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    scored=[]
    for row in range(rows):
        for col in range(cols):
            fill=audit["tile_fills"][row*cols+col]
            blank=1.0-fill
            if blank<0.34 and audit["row_fills"][row]>=row_mean*0.94 and audit["column_fills"][col]>=col_mean*0.94:
                continue
            cx=(col+0.5)/cols
            cy=(row+0.5)/rows
            center_weight=1.0+0.30*(1.0-abs(cx-0.5)*2.0)
            lower_weight=1.0+0.48*max(0.0,cy-0.50)
            interior_weight=0.82 if (row in (0,rows-1) or col in (0,cols-1)) else 1.0
            row_deficit=max(0.0,row_mean-audit["row_fills"][row])
            col_deficit=max(0.0,col_mean-audit["column_fills"][col])
            score=blank*center_weight*lower_weight*interior_weight+row_deficit*0.70+col_deficit*0.45
            if score>0.30:
                scored.append((score,row,col))
    scored.sort(reverse=True)
    tiles=[]
    for _,row,col in scored:
        if (row,col) not in tiles:
            tiles.append((row,col))
        if len(tiles)>=8:
            break
    return tiles

def local_adapter_rescue_cluster_positions(trial, assigned):
    positions=[]
    for pos,_,_,_ in assigned:
        if pos not in positions:
            positions.append(pos)
    pairs,_=layout_overlap_pairs(trial)
    for pair in pairs:
        for pos in pair:
            if pos>=0 and pos not in positions:
                positions.append(pos)
                if len(positions)>=LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT:
                    return positions
    boxes=[]
    for pos,(i,x,y,r,s) in enumerate(trial):
        m=make(i,r,s,gap=True)
        boxes.append((pos,x,y,m.shape[1],m.shape[0]))
    def gap_between(a,b):
        _,ax,ay,aw,ah=a
        _,bx,by,bw,bh=b
        dx=max(0,max(bx-(ax+aw),ax-(bx+bw)))
        dy=max(0,max(by-(ay+ah),ay-(by+bh)))
        return dx+dy
    selected={pos for pos in positions}
    owner_grid=np.full((SH,SW),-1,np.int16)
    for pos,(i,x,y,r,s) in enumerate(trial):
        m=make(i,r,s,gap=True)
        h,w=m.shape
        if x<0 or y<0 or x+w>SW or y+h>SH:
            continue
        owner_region=owner_grid[y:y+h,x:x+w]
        owner_region[m]=pos
    blocker_counts={}
    for pos in list(positions):
        i,x,y,r,s=trial[pos]
        m=make(i,r,s,gap=True)
        h,w=m.shape
        for dy in LOCAL_ADAPTER_FINE_OFFSETS:
            for dx in LOCAL_ADAPTER_FINE_OFFSETS:
                xx=x+dx
                yy=y+dy
                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                    continue
                owner_region=owner_grid[yy:yy+h,xx:xx+w]
                if owner_region.shape!=m.shape:
                    continue
                hit=owner_region[m]
                for blocker in np.unique(hit):
                    blocker=int(blocker)
                    if blocker>=0 and blocker!=pos and blocker not in selected:
                        blocker_counts[blocker]=blocker_counts.get(blocker,0)+int((hit==blocker).sum())
    if blocker_counts:
        seed_boxes=[boxes[pos] for pos in positions]
        blockers=[]
        for pos,count in blocker_counts.items():
            distance=min(gap_between(boxes[pos],seed_box) for seed_box in seed_boxes)
            blockers.append((-count,distance,pos))
        for _,_,pos in sorted(blockers):
            if len(positions)>=LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT:
                return positions
            if pos not in selected:
                positions.append(pos)
                selected.add(pos)
    seed_boxes=[boxes[pos] for pos in positions]
    candidates=[]
    for box in boxes:
        pos=box[0]
        if pos in selected:
            continue
        distance=min(gap_between(box,seed_box) for seed_box in seed_boxes)
        if distance<=max(8,LOCAL_ADAPTER_FINE_RADIUS*3):
            _,x,y,w,h=box
            center_y=y+h/2
            candidates.append((distance,abs(center_y-sum(seed[2]+seed[4]/2 for seed in seed_boxes)/max(1,len(seed_boxes))),pos))
    for _,_,pos in sorted(candidates):
        if len(positions)>=LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT:
            break
        positions.append(pos)
    return positions

def local_adapter_overlap_rescue(trial, assigned):
    if layout_overlap_cells(trial)<=0:
        return trial
    positions=local_adapter_rescue_cluster_positions(trial, assigned)
    if LOCAL_ADAPTER_DEBUG:
        pairs,overlap=layout_overlap_pairs(trial)
        names=[raw[trial[pos][0]][0] for pos in positions]
        print(f"local_adapter_rescue start overlap={overlap} pairs={pairs} positions={positions} names={names}", file=sys.stderr)
    if not positions:
        return None
    assigned_positions={pos for pos,_,_,_ in assigned}
    fixed=build_occ_except_positions(trial,set(positions))
    choices={}
    for pos in positions:
        i,x,y,r,s=trial[pos]
        m=make(i,r,s,gap=True)
        h,w=m.shape
        opts=[]
        for dy in LOCAL_ADAPTER_FINE_OFFSETS:
            for dx in LOCAL_ADAPTER_FINE_OFFSETS:
                xx=x+dx
                yy=y+dy
                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                    continue
                region=fixed[yy:yy+h,xx:xx+w]
                if region.shape!=m.shape or (region&m).any():
                    continue
                opts.append((abs(dx)+abs(dy),xx,yy))
        if not opts:
            return None
        choices[pos]=sorted(opts)[:LOCAL_ADAPTER_OPTIONS]
    order=sorted(positions,key=lambda pos:len(choices[pos]))
    states=[(0,[],fixed.copy())]
    rescue_beam=max(16,min(400,LOCAL_ADAPTER_OPTIONS*16))
    for pos in order:
        i,_,_,r,s=trial[pos]
        m=make(i,r,s,gap=True)
        next_states=[]
        for cost,placed,occ in states:
            for extra,xx,yy in choices[pos]:
                region=occ[yy:yy+m.shape[0],xx:xx+m.shape[1]]
                if region.shape!=m.shape or (region&m).any():
                    continue
                occ2=occ.copy()
                stamp(occ2,xx,yy,m)
                next_states.append((cost+extra,placed+[(pos,xx,yy)],occ2))
        states=sorted(next_states,key=lambda row:row[0])[:rescue_beam]
        if not states:
            return None
    rescued=trial[:]
    for pos,xx,yy in states[0][1]:
        i,_,_,r,s=rescued[pos]
        rescued[pos]=(i,xx,yy,r,s)
    if layout_overlap_cells(rescued)>0:
        if LOCAL_ADAPTER_DEBUG:
            pairs,overlap=layout_overlap_pairs(rescued)
            print(f"local_adapter_rescue failed overlap={overlap} pairs={pairs}", file=sys.stderr)
        return None
    if any(pos not in assigned_positions for pos,_,_ in states[0][1]):
        global LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED
        LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED=True
    if LOCAL_ADAPTER_DEBUG:
        moved=[(pos,xx,yy) for pos,xx,yy in states[0][1] if trial[pos][1]!=xx or trial[pos][2]!=yy]
        print(f"local_adapter_rescue accepted moved={moved}", file=sys.stderr)
    return rescued

def local_adapter_repack(pl, rounds=1, v2_pass=False):
    if not (LOCAL_ADAPTER and MANUAL_STAGGER and pl):
        return pl
    if len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    base_audit=visual_audit_like(pl)
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    infos=[]
    for pos,(i,x,y,r,s) in enumerate(pl):
        m=make(i,r,s,gap=True)
        infos.append((pos,x+m.shape[1]/2,y+m.shape[0]/2,m.shape[1],m.shape[0]))

    best_trial=None
    best_alpha=base_alpha
    best_audit=base_audit
    best_move_count=0
    best_cluster_size=0
    node_count=0
    reject_counts={}
    def reject(reason):
        if LOCAL_ADAPTER_DEBUG:
            reject_counts[reason]=reject_counts.get(reason,0)+1
    target_tiles=[]
    if LOCAL_ADAPTER_TARGET_MODE!="audit_voids":
        target_tiles.extend(local_adapter_target_tiles())
    if LOCAL_ADAPTER_TARGET_MODE in ("audit_voids","hybrid"):
        target_tiles.extend(local_adapter_audit_void_tiles(pl, base_audit))
    if not target_tiles:
        target_tiles=local_adapter_target_tiles()

    seen_tiles=set()
    for row,col in target_tiles:
        if (row,col) in seen_tiles:
            continue
        seen_tiles.add((row,col))
        cx=(col+0.5)*SW/8
        cy=(row+0.5)*SH/10
        near=[pos for _,pos in sorted((abs(ix-cx)+abs(iy-cy),pos) for pos,ix,iy,_,_ in infos)[:LOCAL_ADAPTER_NEAR]]
        cluster_sizes=(3,4)
        for cluster_size in cluster_sizes:
            if not LOCAL_ADAPTER_V2 and cluster_size>3:
                continue
            if cluster_size>LOCAL_ADAPTER_MAX_CLUSTER_SIZE:
                continue
            scale_factors=LOCAL_ADAPTER_V2_SCALE_FACTORS if (LOCAL_ADAPTER_V2 and cluster_size>3) else LOCAL_ADAPTER_SCALE_FACTORS
            if len(near)<cluster_size:
                continue
            for subset in itertools.combinations(near,cluster_size):
                if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                    break
                if not any(pl[p][4]<SCALE_HI[pl[p][0]]-0.003 for p in subset):
                    continue
                fixed=build_occ_except_positions(pl,set(subset))
                cluster_infos=[infos[p] for p in subset]
                x0=max(0,min(v[1]-v[3]*0.9 for v in cluster_infos)-16)
                x1=min(SW,max(v[1]+v[3]*0.9 for v in cluster_infos)+16)
                y0=max(0,min(v[2]-v[4]*0.9 for v in cluster_infos)-16)
                y1=min(SH,max(v[2]+v[4]*0.9 for v in cluster_infos)+16)
                x0=max(0,min(x0,cx-SW*0.18));x1=min(SW,max(x1,cx+SW*0.18))
                y0=max(0,min(y0,cy-SH*0.16));y1=min(SH,max(y1,cy+SH*0.16))
                wall=dil(fixed,1)&(~fixed)
                choices={}
                valid=True
                for pos in subset:
                    i,x,y,r,s=pl[pos]
                    options=[]
                    for ns in sorted(set(round(clamp_scale(i,s*factor),4) for factor in scale_factors), reverse=True):
                        m=make(i,r,ns,gap=True)
                        h,w=m.shape
                        candidates={(x,y)}
                        for dy in LOCAL_ADAPTER_FINE_OFFSETS:
                            for dx in LOCAL_ADAPTER_FINE_OFFSETS:
                                candidates.add((x+dx,y+dy))
                        for yy in range(int(max(0,y0)),int(min(SH-h,y1))+1,3):
                            for xx in range(int(max(0,x0)),int(min(SW-w,x1))+1,3):
                                candidates.add((xx,yy))
                        for xx,yy in candidates:
                            if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                                continue
                            region=fixed[yy:yy+h,xx:xx+w]
                            if region.shape!=m.shape or (region&m).any():
                                continue
                            contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum()))
                            dist=abs((xx+w/2)-cx)+abs((yy+h/2)-cy)
                            moved=abs(xx-x)+abs(yy-y)
                            score=(ns-s)*6000.0+contact*60.0-dist*0.010-moved*0.006
                            options.append((score,xx,yy,ns))
                    options=sorted(options,reverse=True)[:LOCAL_ADAPTER_OPTIONS]
                    if not options:
                        valid=False
                        break
                    choices[pos]=options
                if not valid:
                    continue
                order=sorted(subset,key=lambda pos:len(choices[pos]))
                states=[(0.0,[],fixed.copy())]
                for pos in order:
                    i,_,_,r,_=pl[pos]
                    next_states=[]
                    for score_so_far,assigned,occ in states:
                        for option_score,xx,yy,ns in choices[pos]:
                            node_count+=1
                            if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                                break
                            m=make(i,r,ns,gap=True)
                            region=occ[yy:yy+m.shape[0],xx:xx+m.shape[1]]
                            if region.shape!=m.shape or (region&m).any():
                                continue
                            occ2=occ.copy()
                            stamp(occ2,xx,yy,m)
                            next_states.append((score_so_far+option_score,assigned+[(pos,xx,yy,ns)],occ2))
                        if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                            break
                    states=sorted(next_states,key=lambda row:row[0],reverse=True)[:32]
                    if not states:
                        break
                    if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                        break
                for score,assigned,_ in states[:16]:
                    trial=pl[:]
                    changed=0
                    for pos,xx,yy,ns in assigned:
                        i,x,y,r,s=trial[pos]
                        if xx!=x or yy!=y or abs(ns-s)>0.0001:
                            changed+=1
                        trial[pos]=(i,xx,yy,r,ns)
                    if changed==0:
                        reject("unchanged")
                        continue
                    if layout_overlap_cells(trial)>0:
                        trial=local_adapter_overlap_rescue(trial, assigned)
                        if trial is None or layout_overlap_cells(trial)>0:
                            reject("overlap")
                            continue
                    trial_stats=orientation_stats(trial)
                    if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                        reject("orientation")
                        continue
                    trial_alpha=material_alpha_topup_alpha(trial)
                    if trial_alpha<=best_alpha+0.00001:
                        reject("alpha_not_better")
                        continue
                    trial_accept_threshold=max(LOCAL_ADAPTER_MIN_ACCEPT,base_alpha+LOCAL_ADAPTER_MIN_GAIN)
                    if LOCAL_ADAPTER_V2 and cluster_size>3:
                        trial_accept_threshold=max(trial_accept_threshold,LOCAL_ADAPTER_V2_MIN_ACCEPT)
                    if trial_alpha<trial_accept_threshold-1e-6:
                        reject("alpha_threshold")
                        continue
                    trial_audit=visual_audit_like(trial)
                    if trial_audit["score"]<base_audit["score"]-1:
                        reject("visual_score")
                        continue
                    if trial_audit["large_blank"]>base_audit["large_blank"]+1e-9:
                        reject("large_blank")
                        continue
                    if trial_audit["center_blank"]>base_audit["center_blank"]+0.001:
                        reject("center_blank")
                        continue
                    if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.001:
                        reject("lower_blank")
                        continue
                    if trial_audit["size_cv"]>base_cv+LOCAL_ADAPTER_MAX_SIZE_CV_INCREASE:
                        reject("size_cv")
                        continue
                    if layout_quality(trial)<base_quality-0.070:
                        reject("quality")
                        continue
                    best_trial=trial
                    best_alpha=trial_alpha
                    best_audit=trial_audit
                    best_move_count=changed
                    best_cluster_size=cluster_size
                if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                    break
            if node_count>LOCAL_ADAPTER_NODE_LIMIT:
                break
        if node_count>LOCAL_ADAPTER_NODE_LIMIT:
            break

    if best_trial is not None:
        global LOCAL_ADAPTER_APPLIED, LOCAL_ADAPTER_V2_APPLIED, LOCAL_ADAPTER_MOVES
        if LOCAL_ADAPTER_APPLIED:
            LOCAL_ADAPTER_MOVES+=best_move_count
        else:
            LOCAL_ADAPTER_MOVES=best_move_count
        LOCAL_ADAPTER_APPLIED=True
        LOCAL_ADAPTER_V2_APPLIED=LOCAL_ADAPTER_V2_APPLIED or (LOCAL_ADAPTER_V2 and (v2_pass or best_cluster_size>3))
        if RECOVERY_DEBUG:
            v2_text=" v2=1" if LOCAL_ADAPTER_V2_APPLIED else ""
            print(f"local_adapter accepted moves={best_move_count} cluster={best_cluster_size} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{best_audit['score']}{v2_text}", file=sys.stderr)
        return best_trial
    if LOCAL_ADAPTER_DEBUG:
        print(f"local_adapter rejected v2_pass={int(v2_pass)} base_alpha={base_alpha*100:.3f}% node_count={node_count} rejects={reject_counts}", file=sys.stderr)
    return pl

def structural_micro_grow_relocation_options(pl, pos, fixed, limit):
    i,x,y,r,s=pl[pos]
    scored=[]
    wall=dil(fixed,1)&(~fixed)
    shrink_factors=(1.0,0.997,0.994) if STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK else (1.0,)
    for ns in sorted(set(round(clamp_scale(i,s*factor),4) for factor in shrink_factors), reverse=True):
        m=make(i,r,ns,gap=True)
        h,w=m.shape
        candidates={(min(max(0,x),SW-w),min(max(0,y),SH-h))}
        for dy in range(-STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS,STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS+1):
            for dx in range(-STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS,STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS+1):
                candidates.add((min(max(0,x+dx),SW-w),min(max(0,y+dy),SH-h)))
        for radius in [0,4,8,12,18,24,30,STRUCTURAL_MICRO_GROW_RADIUS]:
            radius=int(radius)
            step=max(1,radius//4)
            for dy in range(-radius,radius+1,step):
                for dx in range(-radius,radius+1,step):
                    if radius and abs(dx)!=radius and abs(dy)!=radius:
                        continue
                    candidates.add((min(max(0,x+dx),SW-w),min(max(0,y+dy),SH-h)))
        for xx,yy in candidates:
            region=fixed[yy:yy+h,xx:xx+w]
            if region.shape!=m.shape or (region&m).any():
                continue
            contact=float((wall[yy:yy+h,xx:xx+w]&m).sum()) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
            moved=abs(xx-x)+abs(yy-y)
            shrink_penalty=max(0.0,s-ns)*max(1,int(make(i,r,s,gap=False).sum()))*0.020
            cx=xx+w/2
            cy=yy+h/2
            void_bonus=0.0
            if SW*0.34<cx<SW*0.62 and SH*0.10<cy<SH*0.36:
                void_bonus+=4.0
            if SW*0.20<cx<SW*0.72 and SH*0.56<cy<SH*0.84:
                void_bonus+=3.0
            scored.append((void_bonus+contact*0.015-moved*0.045-shrink_penalty,xx,yy,ns))
    scored.sort(reverse=True)
    return [(xx,yy,ns) for _,xx,yy,ns in scored[:limit]]

def structural_micro_grow(pl, rounds=1):
    if not (STRUCTURAL_MICRO_GROW and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    accept_threshold=max(STRUCTURAL_MICRO_GROW_MIN_ACCEPT,base_alpha+STRUCTURAL_MICRO_GROW_MIN_GAIN)
    if base_alpha>=accept_threshold-1e-6:
        return pl
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    best_trial=None
    best_alpha=base_alpha
    best_move_count=0
    node_count=0
    current=pl[:]
    factors=[1.003,1.006,1.009,1.012,1.015,1.018,1.022,1.026,1.030]
    offsets=[0]
    for step in range(1,9):
        offsets.extend([-step,step])

    target_scores=[]
    for pos,(i,x,y,r,s) in enumerate(current):
        headroom=max(0.0,SCALE_HI[i]-s)
        if headroom<0.003:
            continue
        m=make(i,r,s,gap=True)
        cm=make(i,r,s,gap=False)
        cx=x+m.shape[1]/2
        cy=y+m.shape[0]/2
        void_weight=1.0
        if SW*0.34<cx<SW*0.62 and SH*0.10<cy<SH*0.36:
            void_weight=1.8
        if SW*0.20<cx<SW*0.72 and SH*0.56<cy<SH*0.84:
            void_weight=max(void_weight,2.4)
        target_scores.append((headroom*max(1,int(cm.sum()))*void_weight,pos))
    target_order=[pos for _,pos in sorted(target_scores,reverse=True)[:16]]

    for _ in range(max(1,rounds)):
        for pos in target_order:
            i,x,y,r,s=current[pos]
            old=make(i,r,s,gap=True)
            cx=x+old.shape[1]/2
            cy=y+old.shape[0]/2
            for factor in factors:
                ns=round(clamp_scale(i,s*factor),4)
                if ns<=s+0.0004:
                    continue
                m=make(i,r,ns,gap=True)
                h,w=m.shape
                if h>SH or w>SW:
                    continue
                base_x=int(round(cx-w/2))
                base_y=int(round(cy-h/2))
                for dy in offsets:
                    for dx in offsets:
                        if node_count>STRUCTURAL_MICRO_GROW_NODE_LIMIT:
                            break
                        nx=min(max(0,base_x+dx),SW-w)
                        ny=min(max(0,base_y+dy),SH-h)
                        blockers=mask_overlap_blockers(current,pos,nx,ny,m)
                        node_count+=1
                        if blockers is None or len(blockers)>STRUCTURAL_MICRO_GROW_MAX_BLOCKERS:
                            continue
                        fixed=build_occ_except_positions(current,set([pos]+blockers))
                        region=fixed[ny:ny+h,nx:nx+w]
                        if region.shape!=m.shape or (region&m).any():
                            continue
                        fixed_with_grow=fixed.copy()
                        stamp(fixed_with_grow,nx,ny,m)
                        states=[(0,[],fixed_with_grow)]
                        valid=True
                        options={}
                        for blocker in blockers:
                            opts=structural_micro_grow_relocation_options(current,blocker,fixed_with_grow,STRUCTURAL_MICRO_GROW_OPTIONS)
                            if not opts:
                                valid=False
                                break
                            options[blocker]=opts
                        if not valid:
                            continue
                        for blocker in sorted(blockers,key=lambda pp:len(options[pp])):
                            bi,_,_,br,bs=current[blocker]
                            next_states=[]
                            for move_cost,placed,occ in states:
                                for xx,yy,bns in options[blocker]:
                                    bm=make(bi,br,bns,gap=True)
                                    bh,bw=bm.shape
                                    reg=occ[yy:yy+bh,xx:xx+bw]
                                    if reg.shape!=bm.shape or (reg&bm).any():
                                        continue
                                    occ2=occ.copy()
                                    stamp(occ2,xx,yy,bm)
                                    ox,oy=current[blocker][1],current[blocker][2]
                                    next_states.append((move_cost+abs(xx-ox)+abs(yy-oy),placed+[(blocker,xx,yy,bns)],occ2))
                            states=sorted(next_states,key=lambda row:row[0])[:80]
                            if not states:
                                break
                        for move_cost,placed,_ in states[:20]:
                            trial=current[:]
                            trial[pos]=(i,nx,ny,r,ns)
                            changed=1 if (nx!=x or ny!=y or abs(ns-s)>0.0001) else 0
                            for blocker,xx,yy,bns in placed:
                                bi,bx,by,br,bs=trial[blocker]
                                trial[blocker]=(bi,xx,yy,br,bns)
                                if xx!=bx or yy!=by or abs(bns-bs)>0.0001:
                                    changed+=1
                            if changed==0:
                                continue
                            if layout_overlap_cells(trial)>0:
                                continue
                            trial_stats=orientation_stats(trial)
                            if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                continue
                            trial_alpha=material_alpha_topup_alpha(trial)
                            if trial_alpha<=best_alpha+0.00001:
                                continue
                            trial_audit=visual_audit_like(trial)
                            if trial_audit["score"]<base_audit["score"]-1:
                                continue
                            if trial_audit["large_blank"]>base_audit["large_blank"]+0.002:
                                continue
                            if trial_audit["center_blank"]>base_audit["center_blank"]+0.002:
                                continue
                            if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.002:
                                continue
                            if trial_audit["size_cv"]>base_cv+0.006:
                                continue
                            if layout_quality(trial)<base_quality-0.070:
                                continue
                            best_trial=trial
                            best_alpha=trial_alpha
                            best_move_count=changed
                    if node_count>STRUCTURAL_MICRO_GROW_NODE_LIMIT:
                        break
                if node_count>STRUCTURAL_MICRO_GROW_NODE_LIMIT:
                    break
            if node_count>STRUCTURAL_MICRO_GROW_NODE_LIMIT:
                break
        if best_trial is not None:
            break

    if best_trial is not None and best_alpha>=accept_threshold-1e-6:
        global STRUCTURAL_MICRO_GROW_APPLIED, STRUCTURAL_MICRO_GROW_MOVES
        STRUCTURAL_MICRO_GROW_APPLIED=True
        STRUCTURAL_MICRO_GROW_MOVES=best_move_count
        if RECOVERY_DEBUG:
            print(f"structural_micro_grow accepted moves={best_move_count} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{visual_audit_like(best_trial)['score']}", file=sys.stderr)
        return best_trial
    if RECOVERY_DEBUG and STRUCTURAL_MICRO_GROW:
        print(f"structural_micro_grow rejected base_alpha={base_alpha*100:.3f}% accept={accept_threshold*100:.3f}% node_count={node_count} best_alpha={best_alpha*100:.3f}%", file=sys.stderr)
    return pl

def scale_transfer_repack(pl, rounds=1):
    if not (SCALE_TRANSFER and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    accept_threshold=max(SCALE_TRANSFER_MIN_ACCEPT,base_alpha+SCALE_TRANSFER_MIN_GAIN)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    masks=[make(i,r,s,gap=True) for i,_,_,r,s in current]
    contents=[max(1,int(make(i,r,s,gap=False).sum())) for i,_,_,r,s in current]
    centers=[(x+masks[pos].shape[1]/2,y+masks[pos].shape[0]/2) for pos,(_,x,y,_,_) in enumerate(current)]
    grow_factors=(1.003,1.006,1.009,1.012,1.015,1.018,1.024)
    shrink_factors=(0.997,0.994,0.991,0.988,0.985,0.980)
    shrink_offsets=(0,-1,1,-2,2)
    grow_offsets=(0,-1,1,-2,2,-3,3,-4,4,-6,6,-8,8)
    best_trial=None
    best_alpha=base_alpha
    best_audit=base_audit
    best_gain=0.0
    node_count=0

    for _ in range(max(1,rounds)):
        for grow_pos,(gi,gx,gy,gr,gs) in enumerate(current):
            if node_count>SCALE_TRANSFER_NODE_LIMIT:
                break
            grow_variants=[]
            for factor in grow_factors:
                ns=round(clamp_scale(gi,gs*factor),4)
                if ns<=gs+0.0004:
                    continue
                gm=make(gi,gr,ns,gap=True)
                gc=max(1,int(make(gi,gr,ns,gap=False).sum()))
                if gc<=contents[grow_pos]:
                    continue
                grow_variants.append((factor,ns,gm,gc))
            if not grow_variants:
                continue
            gcx,gcy=centers[grow_pos]
            near=[
                pos for _,pos in sorted(
                    (abs(centers[pos][0]-gcx)+abs(centers[pos][1]-gcy),pos)
                    for pos in range(len(current)) if pos!=grow_pos
                )[:SCALE_TRANSFER_NEAR]
            ]
            for shrink_pos in near:
                if node_count>SCALE_TRANSFER_NODE_LIMIT:
                    break
                si,sx,sy,sr,ss=current[shrink_pos]
                shrink_variants=[]
                for factor in shrink_factors:
                    ns=round(clamp_scale(si,ss*factor),4)
                    if ns>=ss-0.0004:
                        continue
                    sm=make(si,sr,ns,gap=True)
                    sc=max(1,int(make(si,sr,ns,gap=False).sum()))
                    if sc>=contents[shrink_pos]:
                        continue
                    shrink_variants.append((factor,ns,sm,sc))
                if not shrink_variants:
                    continue
                fixed=build_occ_except_positions(current,{grow_pos,shrink_pos})
                for _,shrink_scale,sm,shrink_content in shrink_variants:
                    if node_count>SCALE_TRANSFER_NODE_LIMIT:
                        break
                    sh,sw=sm.shape
                    for sdy in shrink_offsets:
                        for sdx in shrink_offsets:
                            if node_count>SCALE_TRANSFER_NODE_LIMIT:
                                break
                            nsx=min(max(0,sx+sdx),SW-sw)
                            nsy=min(max(0,sy+sdy),SH-sh)
                            node_count+=1
                            region=fixed[nsy:nsy+sh,nsx:nsx+sw]
                            if region.shape!=sm.shape or (region&sm).any():
                                continue
                            fixed_with_shrink=fixed.copy()
                            stamp(fixed_with_shrink,nsx,nsy,sm)
                            for _,grow_scale,gm,grow_content in grow_variants:
                                gh,gw=gm.shape
                                for gdy in grow_offsets:
                                    for gdx in grow_offsets:
                                        if node_count>SCALE_TRANSFER_NODE_LIMIT:
                                            break
                                        ngx=min(max(0,gx+gdx),SW-gw)
                                        ngy=min(max(0,gy+gdy),SH-gh)
                                        node_count+=1
                                        region=fixed_with_shrink[ngy:ngy+gh,ngx:ngx+gw]
                                        if region.shape!=gm.shape or (region&gm).any():
                                            continue
                                        trial=current[:]
                                        trial[shrink_pos]=(si,nsx,nsy,sr,shrink_scale)
                                        trial[grow_pos]=(gi,ngx,ngy,gr,grow_scale)
                                        if layout_overlap_cells(trial)>0:
                                            continue
                                        trial_stats=orientation_stats(trial)
                                        if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                            continue
                                        trial_alpha=material_alpha_topup_alpha(trial)
                                        if trial_alpha<=best_alpha+0.00001 or trial_alpha<accept_threshold-1e-6:
                                            continue
                                        trial_audit=visual_audit_like(trial)
                                        if trial_audit["score"]<base_audit["score"]-1:
                                            continue
                                        if trial_audit["large_blank"]>base_audit["large_blank"]+0.002:
                                            continue
                                        if trial_audit["center_blank"]>base_audit["center_blank"]+0.002:
                                            continue
                                        if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.002:
                                            continue
                                        if trial_audit["size_cv"]>base_cv+0.006:
                                            continue
                                        if layout_quality(trial)<base_quality-0.070:
                                            continue
                                        grow_gain=(grow_content-contents[grow_pos])-(contents[shrink_pos]-shrink_content)
                                        move_cost=abs(ngx-gx)+abs(ngy-gy)+abs(nsx-sx)+abs(nsy-sy)
                                        score=(trial_alpha-base_alpha)*100000.0 + grow_gain*0.010 - move_cost*0.020
                                        if score>best_gain:
                                            best_trial=trial
                                            best_alpha=trial_alpha
                                            best_audit=trial_audit
                                            best_gain=score
            if best_trial is not None and best_alpha>=accept_threshold-1e-6:
                break
        if best_trial is not None and best_alpha>=accept_threshold-1e-6:
            break

    if best_trial is not None and best_alpha>=accept_threshold-1e-6:
        global SCALE_TRANSFER_APPLIED, SCALE_TRANSFER_MOVES
        SCALE_TRANSFER_APPLIED=True
        SCALE_TRANSFER_MOVES=2
        if RECOVERY_DEBUG:
            print(f"scale_transfer accepted moves=2 alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{best_audit['score']} node_count={node_count}", file=sys.stderr)
        return best_trial
    if RECOVERY_DEBUG and SCALE_TRANSFER:
        print(f"scale_transfer rejected base_alpha={base_alpha*100:.3f}% accept={accept_threshold*100:.3f}% node_count={node_count}", file=sys.stderr)
    return pl

def small_group_material_repack_targets(pl, audit, limit=None):
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    scored=[]
    for row in range(rows):
        for col in range(cols):
            fill=audit["tile_fills"][row*cols+col]
            blank=1.0-fill
            if blank<0.30 and audit["row_fills"][row]>=row_mean*0.95 and audit["column_fills"][col]>=col_mean*0.95:
                continue
            cx=(col+0.5)/cols
            cy=(row+0.5)/rows
            interior=0.72 if row in (0,rows-1) or col in (0,cols-1) else 1.0
            center=1.0+0.35*(1.0-abs(cx-0.5)*2.0)
            lower=1.0+0.38*max(0.0,cy-0.52)
            row_deficit=max(0.0,row_mean-audit["row_fills"][row])
            col_deficit=max(0.0,col_mean-audit["column_fills"][col])
            score=blank*interior*center*lower+row_deficit*0.68+col_deficit*0.44
            if score>0.28:
                scored.append((score,row,col))
    scored.sort(reverse=True)
    out=[]
    for _,row,col in scored:
        if (row,col) not in out:
            out.append((row,col))
        if len(out)>=(limit or SMALL_GROUP_MATERIAL_REPACK_TARGETS):
            break
    return out

def small_group_material_repack(pl, rounds=1):
    if not (SMALL_GROUP_MATERIAL_REPACK and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    accept_threshold=max(SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT,base_alpha+SMALL_GROUP_MATERIAL_REPACK_MIN_GAIN)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    masks=[make(i,r,s,gap=True) for i,_,_,r,s in current]
    content_areas=[max(1,int(make(i,r,s,gap=False).sum())) for i,_,_,r,s in current]
    infos=[]
    for pos,(i,x,y,r,s) in enumerate(current):
        m=masks[pos]
        infos.append((pos,x+m.shape[1]/2,y+m.shape[0]/2,m.shape[1],m.shape[0]))

    best_trial=None
    best_alpha=base_alpha
    best_move_count=0
    node_count=0
    scale_factors=(1.0,1.003,1.006,1.009,1.012,1.015)

    for _ in range(max(1,rounds)):
        for row,col in small_group_material_repack_targets(current,base_audit,SMALL_GROUP_MATERIAL_REPACK_TARGETS):
            if node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                break
            cx=(col+0.5)*SW/8
            cy=(row+0.5)*SH/10
            near=[pos for _,pos in sorted((abs(ix-cx)+abs(iy-cy),pos) for pos,ix,iy,_,_ in infos)[:SMALL_GROUP_MATERIAL_REPACK_NEAR]]
            for cluster_size in range(3,SMALL_GROUP_MATERIAL_REPACK_MAX_CLUSTER_SIZE+1):
                if node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                    break
                if len(near)<cluster_size:
                    continue
                subset_count=0
                for subset in itertools.combinations(near,cluster_size):
                    subset_count+=1
                    if subset_count>12:
                        break
                    if node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                        break
                    growable=[pos for pos in subset if current[pos][4]<SCALE_HI[current[pos][0]]-0.002]
                    if not growable:
                        continue
                    fixed=build_occ_except_positions(current,set(subset))
                    cluster_infos=[infos[p] for p in subset]
                    x0=max(0,min(v[1]-v[3]*1.05 for v in cluster_infos)-20)
                    x1=min(SW,max(v[1]+v[3]*1.05 for v in cluster_infos)+20)
                    y0=max(0,min(v[2]-v[4]*1.05 for v in cluster_infos)-20)
                    y1=min(SH,max(v[2]+v[4]*1.05 for v in cluster_infos)+20)
                    x0=max(0,min(x0,cx-SW*0.22));x1=min(SW,max(x1,cx+SW*0.22))
                    y0=max(0,min(y0,cy-SH*0.20));y1=min(SH,max(y1,cy+SH*0.20))
                    wall=dil(fixed,1)&(~fixed)
                    choices={}
                    valid=True
                    for pos in subset:
                        i,x,y,r,s=current[pos]
                        pos_factors=scale_factors if pos in growable else (1.0,)
                        options=[]
                        for ns in sorted(set(round(clamp_scale(i,s*factor),4) for factor in pos_factors), reverse=True):
                            m=make(i,r,ns,gap=True)
                            h,w=m.shape
                            candidates={(x,y)}
                            for dy in (-6,-4,-2,0,2,4,6):
                                for dx in (-6,-4,-2,0,2,4,6):
                                    candidates.add((x+dx,y+dy))
                            for yy in range(int(max(0,y0)),int(min(SH-h,y1))+1,4):
                                for xx in range(int(max(0,x0)),int(min(SW-w,x1))+1,4):
                                    candidates.add((xx,yy))
                            for xx,yy in candidates:
                                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                                    continue
                                region=fixed[yy:yy+h,xx:xx+w]
                                if region.shape!=m.shape or (region&m).any():
                                    continue
                                contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum())) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
                                moved=abs(xx-x)+abs(yy-y)
                                dist=abs((xx+w/2)-cx)+abs((yy+h/2)-cy)
                                grow=max(0.0,ns-s)
                                score=grow*content_areas[pos]*0.42+contact*58.0-dist*0.012-moved*0.010
                                if grow>0:
                                    score+=16.0
                                options.append((score,xx,yy,ns))
                        options=sorted(options,reverse=True)[:SMALL_GROUP_MATERIAL_REPACK_OPTIONS]
                        if not options:
                            valid=False
                            break
                        choices[pos]=options
                    if not valid:
                        continue
                    order=sorted(subset,key=lambda pos:len(choices[pos]))
                    states=[(0.0,[],fixed.copy())]
                    for pos in order:
                        i,_,_,r,_=current[pos]
                        next_states=[]
                        for score_so_far,assigned,occ in states:
                            for option_score,xx,yy,ns in choices[pos]:
                                node_count+=1
                                if node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                                    break
                                m=make(i,r,ns,gap=True)
                                region=occ[yy:yy+m.shape[0],xx:xx+m.shape[1]]
                                if region.shape!=m.shape or (region&m).any():
                                    continue
                                occ2=occ.copy()
                                stamp(occ2,xx,yy,m)
                                next_states.append((score_so_far+option_score,assigned+[(pos,xx,yy,ns)],occ2))
                            if node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                                break
                        states=sorted(next_states,key=lambda entry:entry[0],reverse=True)[:36]
                        if not states or node_count>SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT:
                            break
                    for score,assigned,_ in states[:18]:
                        trial=current[:]
                        changed=0
                        grown=0
                        for pos,xx,yy,ns in assigned:
                            i,x,y,r,s=trial[pos]
                            if xx!=x or yy!=y or abs(ns-s)>0.0001:
                                changed+=1
                            if ns>s+0.0004:
                                grown+=1
                            trial[pos]=(i,xx,yy,r,ns)
                        if changed==0 or grown==0:
                            continue
                        if layout_overlap_cells(trial)>0:
                            continue
                        trial_stats=orientation_stats(trial)
                        if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                            continue
                        trial_alpha=material_alpha_topup_alpha(trial)
                        if trial_alpha<=best_alpha+0.00001 or trial_alpha<accept_threshold-1e-6:
                            continue
                        trial_audit=visual_audit_like(trial)
                        if trial_audit["score"]<base_audit["score"]-1:
                            continue
                        if trial_audit["large_blank"]>base_audit["large_blank"]+0.002:
                            continue
                        if trial_audit["center_blank"]>base_audit["center_blank"]+0.002:
                            continue
                        if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.002:
                            continue
                        if trial_audit["size_cv"]>base_cv+SMALL_GROUP_MATERIAL_REPACK_MAX_SIZE_CV_INCREASE:
                            continue
                        if layout_quality(trial)<base_quality-0.070:
                            continue
                        best_trial=trial
                        best_alpha=trial_alpha
                        best_move_count=changed
        if best_trial is not None:
            break

    if best_trial is not None:
        global SMALL_GROUP_MATERIAL_REPACK_APPLIED, SMALL_GROUP_MATERIAL_REPACK_MOVES
        SMALL_GROUP_MATERIAL_REPACK_APPLIED=True
        SMALL_GROUP_MATERIAL_REPACK_MOVES=best_move_count
        if RECOVERY_DEBUG:
            after=visual_audit_like(best_trial)
            print(f"small_group_material_repack accepted moves={best_move_count} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{after['score']} node_count={node_count}", file=sys.stderr)
        return best_trial
    if RECOVERY_DEBUG and SMALL_GROUP_MATERIAL_REPACK:
        print(f"small_group_material_repack rejected base_alpha={base_alpha*100:.3f}% accept={accept_threshold*100:.3f}% node_count={node_count}", file=sys.stderr)
    return pl

def band_void_fill_targets(audit, limit=None):
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    scored=[]
    for row in range(2,rows):
        for col in range(1,cols-1):
            fill=audit["tile_fills"][row*cols+col]
            blank=1.0-fill
            if blank<0.30 and audit["row_fills"][row]>=row_mean*0.94 and audit["column_fills"][col]>=col_mean*0.94:
                continue
            cx=(col+0.5)/cols
            cy=(row+0.5)/rows
            center=1.0+0.50*(1.0-abs(cx-0.5)*2.0)
            lower=1.0+0.72*max(0.0,cy-0.48)
            row_deficit=max(0.0,row_mean-audit["row_fills"][row])
            col_deficit=max(0.0,col_mean-audit["column_fills"][col])
            edge_penalty=0.62 if row==rows-1 else 1.0
            score=(blank*center*lower+row_deficit*0.82+col_deficit*0.48)*edge_penalty
            if score>0.34:
                scored.append((score,row,col))
    scored.sort(reverse=True)
    return [(row,col) for _,row,col in scored[:(limit or BAND_VOID_FILL_TARGETS)]]

def band_void_fill_donors(pl, audit, cx, cy, limit=None):
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    areas=[max(1,int(make(i,r,s,gap=False).sum())) for i,_,_,r,s in pl]
    median_area=float(np.median(np.array(areas))) if areas else 1.0
    scored=[]
    for pos,(i,x,y,r,s) in enumerate(pl):
        headroom=max(0.0,SCALE_HI[i]-s)
        if headroom<0.002:
            continue
        m=make(i,r,s,gap=True)
        px=x+m.shape[1]/2
        py=y+m.shape[0]/2
        row=min(rows-1,max(0,int(py*rows/max(1,SH))))
        col=min(cols-1,max(0,int(px*cols/max(1,SW))))
        target_dist=abs(px-cx)+abs(py-cy)
        if target_dist<max(m.shape[0],m.shape[1])*0.70:
            continue
        area=areas[pos]
        small_medium=max(0.0,(median_area*1.18-area)/max(1.0,median_area))*0.85
        not_huge=0.35 if area<=median_area*1.30 else -0.45
        edge_bonus=0.0
        if row<=2:
            edge_bonus+=0.55
        if col in (0,cols-1):
            edge_bonus+=0.35
        if row>=rows-2:
            edge_bonus-=0.18
        dense_bonus=max(0.0,audit["row_fills"][row]-row_mean)*0.90+max(0.0,audit["column_fills"][col]-col_mean)*0.55
        score=headroom*18.0+small_medium+not_huge+edge_bonus+dense_bonus-target_dist*0.0014
        scored.append((score,pos))
    scored.sort(reverse=True)
    return [pos for _,pos in scored[:(limit or BAND_VOID_FILL_DONORS)]]

def band_void_fill_backfills(pl, audit, mover_pos, old_cx, old_cy, limit=None):
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    areas=[max(1,int(make(i,r,s,gap=False).sum())) for i,_,_,r,s in pl]
    median_area=float(np.median(np.array(areas))) if areas else 1.0
    donor_row=min(rows-1,max(0,int(old_cy*rows/max(1,SH))))
    donor_col=min(cols-1,max(0,int(old_cx*cols/max(1,SW))))
    scored=[]
    for pos,(i,x,y,r,s) in enumerate(pl):
        if pos==mover_pos:
            continue
        m=make(i,r,s,gap=True)
        px=x+m.shape[1]/2
        py=y+m.shape[0]/2
        row=min(rows-1,max(0,int(py*rows/max(1,SH))))
        col=min(cols-1,max(0,int(px*cols/max(1,SW))))
        if abs(row-donor_row)>1:
            continue
        dist=abs(px-old_cx)+abs(py-old_cy)
        if dist>max(SW,SH)*0.38:
            continue
        area=areas[pos]
        headroom=max(0.0,SCALE_HI[i]-s)
        small_medium=max(0.0,(median_area*1.12-area)/max(1.0,median_area))*0.55
        dense=max(0.0,audit["row_fills"][row]-row_mean)*0.80+max(0.0,audit["column_fills"][col]-col_mean)*0.42
        row_fit=0.35 if row==donor_row else 0.10
        col_fit=0.18 if abs(col-donor_col)<=1 else 0.0
        score=headroom*8.0+small_medium+dense+row_fit+col_fit-dist*0.0045
        scored.append((score,pos))
    scored.sort(reverse=True)
    return [pos for _,pos in scored[:(limit or BAND_VOID_FILL_PAIR_BACKFILLS)]]

def band_void_fill_pair_relocate(pl, rounds=1):
    if not (LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR and LOW_ALPHA_READABLE_BAND_VOID_FILL and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    best_trial=None
    best_alpha=base_alpha
    best_move_count=0
    node_count=0
    trial_count=0
    debug_best=None
    mover_factors=(1.0,0.996,0.992)
    backfill_factors=(1.006,1.0,0.996,0.992)

    def guided_options(pos, fixed, target_cx, target_cy, factors, row_strength, limit):
        nonlocal node_count
        i,x,y,r,s=current[pos]
        old_m=make(i,r,s,gap=True)
        old_cx=x+old_m.shape[1]/2
        old_cy=y+old_m.shape[0]/2
        wall=dil(fixed,1)&(~fixed)
        options=[]
        for factor in factors:
            ns=round(clamp_scale(i,s*factor),4)
            if ns<s-0.006:
                continue
            if abs(ns-s)<0.0001 and abs(factor-1.0)>0.0001:
                continue
            m=make(i,r,ns,gap=True)
            h,w=m.shape
            if h>SH or w>SW:
                continue
            desired_x=int(round(target_cx-w/2))
            desired_y=int(round(target_cy-h/2))
            candidates=set()
            if node_count>=BAND_VOID_FILL_PAIR_NODE_LIMIT:
                break
            guided=place_guided(fixed,m,desired_x,desired_y,row_strength=row_strength)
            node_count+=1
            if guided is not None:
                candidates.add(guided)
            for radius in (0,4,8,12,18,24):
                step=max(4,radius or 4)
                for dy in range(-radius,radius+1,step):
                    for dx in range(-radius,radius+1,step):
                        if radius and abs(dx)!=radius and abs(dy)!=radius:
                            continue
                        xx=min(max(0,desired_x+dx),SW-w)
                        yy=min(max(0,desired_y+dy),SH-h)
                        candidates.add((xx,yy))
            for xx,yy in candidates:
                node_count+=1
                if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                    break
                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                    continue
                region=fixed[yy:yy+h,xx:xx+w]
                if region.shape!=m.shape or (region&m).any():
                    continue
                contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum())) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
                move=abs((xx+w/2)-old_cx)+abs((yy+h/2)-old_cy)
                target_dist=abs((xx+w/2)-target_cx)+abs((yy+h/2)-target_cy)
                grow=max(0.0,ns-s)
                score=grow*max(1,int(make(i,r,s,gap=False).sum()))*0.28+contact*66.0-target_dist*0.024-move*0.010
                options.append((score,xx,yy,ns))
            if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                break
        return sorted(options,reverse=True)[:limit]

    for _ in range(max(1,rounds)):
        current_audit=visual_audit_like(current)
        for row,col in band_void_fill_targets(current_audit,BAND_VOID_FILL_TARGETS):
            if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                break
            target_cx=(col+0.5)*SW/8
            target_cy=(row+0.5)*SH/10
            donors=band_void_fill_donors(current,current_audit,target_cx,target_cy,BAND_VOID_FILL_DONORS)
            for mover in donors:
                if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                    break
                mi,mx,my,mr,ms=current[mover]
                old_m=make(mi,mr,ms,gap=True)
                old_cx=mx+old_m.shape[1]/2
                old_cy=my+old_m.shape[0]/2
                donor_row=min(9,max(0,int(old_cy*10/max(1,SH))))
                backfills=band_void_fill_backfills(current,current_audit,mover,old_cx,old_cy,BAND_VOID_FILL_PAIR_BACKFILLS)
                for backfill in backfills:
                    if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                        break
                    fixed=build_occ_except_positions(current,{mover,backfill})
                    mover_options=guided_options(mover,fixed,target_cx,target_cy,mover_factors,2.20,min(10,BAND_VOID_FILL_OPTIONS))
                    for _,nx,ny,ns in mover_options:
                        if node_count>BAND_VOID_FILL_PAIR_NODE_LIMIT:
                            break
                        mover_mask=make(mi,mr,ns,gap=True)
                        occ=fixed.copy()
                        stamp(occ,nx,ny,mover_mask)
                        backfill_options=guided_options(backfill,occ,old_cx,old_cy,backfill_factors,1.85,min(10,BAND_VOID_FILL_OPTIONS))
                        bi,bx,by,br,bs=current[backfill]
                        for _,bxx,byy,bns in backfill_options:
                            trial=current[:]
                            trial[mover]=(mi,nx,ny,mr,ns)
                            trial[backfill]=(bi,bxx,byy,br,bns)
                            changed=0
                            if nx!=mx or ny!=my or abs(ns-ms)>0.0001:
                                changed+=1
                            if bxx!=bx or byy!=by or abs(bns-bs)>0.0001:
                                changed+=1
                            if changed<2:
                                continue
                            if layout_overlap_cells(trial)>0:
                                continue
                            trial_count+=1
                            trial_stats=orientation_stats(trial)
                            if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                                continue
                            trial_alpha=material_alpha_topup_alpha(trial)
                            if trial_alpha<base_alpha-0.00010:
                                continue
                            trial_audit=visual_audit_like(trial)
                            center_gain=base_audit["center_blank"]-trial_audit["center_blank"]
                            lower_gain=base_audit["lower_blank"]-trial_audit["lower_blank"]
                            void_gain=max(0.0,center_gain)+max(0.0,lower_gain)*1.25
                            target_tile_gain=trial_audit["tile_fills"][row*8+col]-base_audit["tile_fills"][row*8+col]
                            donor_row_loss=base_audit["row_fills"][donor_row]-trial_audit["row_fills"][donor_row]
                            if RECOVERY_DEBUG:
                                near_score=(trial_alpha-base_alpha)*900.0+void_gain*5.0+target_tile_gain*3.0-donor_row_loss*2.5+(trial_audit["selection"]-base_audit["selection"])*0.000001
                                if debug_best is None or near_score>debug_best[0]:
                                    debug_best=(near_score,trial_alpha,void_gain,center_gain,lower_gain,target_tile_gain,donor_row_loss,trial_audit["score"],trial_audit["large_blank"],trial_audit["size_cv"])
                            if void_gain<BAND_VOID_FILL_PAIR_MIN_VOID_GAIN and target_tile_gain<0.018:
                                continue
                            if donor_row_loss>0.025:
                                continue
                            if trial_audit["row_imbalance"]>base_audit["row_imbalance"]+0.035:
                                continue
                            if trial_audit["score"]<base_audit["score"]-2:
                                continue
                            if trial_audit["large_blank"]>base_audit["large_blank"]+0.006:
                                continue
                            if trial_audit["center_blank"]>base_audit["center_blank"]+0.003:
                                continue
                            if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.003:
                                continue
                            if trial_audit["size_cv"]>base_cv+0.010:
                                continue
                            if layout_quality(trial)<base_quality-0.090:
                                continue
                            move=abs((nx+make(mi,mr,ns,gap=True).shape[1]/2)-old_cx)+abs((ny+make(mi,mr,ns,gap=True).shape[0]/2)-old_cy)
                            back_move=abs((bxx+make(bi,br,bns,gap=True).shape[1]/2)-(bx+make(bi,br,bs,gap=True).shape[1]/2))+abs((byy+make(bi,br,bns,gap=True).shape[0]/2)-(by+make(bi,br,bs,gap=True).shape[0]/2))
                            score=(trial_alpha-base_alpha)*120000.0+void_gain*5200.0+target_tile_gain*3600.0+(trial_audit["selection"]-base_audit["selection"])*0.0010-donor_row_loss*900.0-(move+back_move)*0.010
                            if best_trial is None or score>best_trial[0]:
                                best_trial=(score,trial,trial_alpha,changed)
                if best_trial is not None:
                    break
            if best_trial is not None:
                break
        if best_trial is not None:
            break

    if best_trial is not None:
        _,trial,best_alpha,best_move_count=best_trial
        global BAND_VOID_FILL_PAIR_APPLIED, BAND_VOID_FILL_PAIR_MOVES
        BAND_VOID_FILL_PAIR_APPLIED=True
        BAND_VOID_FILL_PAIR_MOVES=best_move_count
        if RECOVERY_DEBUG:
            after=visual_audit_like(trial)
            print(f"band_void_fill_pair accepted moves={best_move_count} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{after['score']} centerBlank={base_audit['center_blank']:.3f}->{after['center_blank']:.3f} lowerBlank={base_audit['lower_blank']:.3f}->{after['lower_blank']:.3f} node_count={node_count}", file=sys.stderr)
        return trial
    if RECOVERY_DEBUG and LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR:
        if debug_best is not None:
            _,dbg_alpha,dbg_void,dbg_center,dbg_lower,dbg_tile,dbg_row_loss,dbg_score,dbg_large,dbg_cv=debug_best
            print(f"band_void_fill_pair rejected base_alpha={base_alpha*100:.3f}% minVoid={BAND_VOID_FILL_PAIR_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count} best_alpha={dbg_alpha*100:.3f}% best_void_gain={dbg_void:.4f} center_gain={dbg_center:.4f} lower_gain={dbg_lower:.4f} target_tile_gain={dbg_tile:.4f} donor_row_loss={dbg_row_loss:.4f} best_visual={dbg_score} best_large={dbg_large:.4f} best_cv={dbg_cv:.4f}", file=sys.stderr)
        else:
            print(f"band_void_fill_pair rejected base_alpha={base_alpha*100:.3f}% minVoid={BAND_VOID_FILL_PAIR_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count}", file=sys.stderr)
    return pl

def right_center_void_metrics(audit):
    rows=10
    cols=8
    def blank_for(row_range, col_range):
        vals=[]
        for row in row_range:
            for col in col_range:
                if 0<=row<rows and 0<=col<cols:
                    vals.append(1.0-audit["tile_fills"][row*cols+col])
        return sum(vals)/max(1,len(vals))
    return {
        "right_blank":blank_for(range(2,9),range(6,8)),
        "mid_right_blank":blank_for(range(2,8),range(4,7)),
    }

def right_center_void_targets(audit, limit=None):
    rows=10
    cols=8
    row_mean=sum(audit["row_fills"])/max(1,len(audit["row_fills"]))
    col_mean=sum(audit["column_fills"])/max(1,len(audit["column_fills"]))
    scored=[]
    for row in range(2,9):
        for col in range(4,cols):
            fill=audit["tile_fills"][row*cols+col]
            blank=1.0-fill
            if blank<0.24 and audit["column_fills"][col]>=col_mean*0.96:
                continue
            cx=(col+0.5)/cols
            cy=(row+0.5)/rows
            right_weight=1.0+0.48*max(0.0,(cx-0.50)/0.4375)
            center_weight=1.0+0.32*(1.0-abs(cx-0.64)*2.0)
            vertical_weight=1.0+0.25*(1.0-abs(cy-0.58)*2.0)
            row_deficit=max(0.0,row_mean-audit["row_fills"][row])
            col_deficit=max(0.0,col_mean-audit["column_fills"][col])
            edge_penalty=0.86 if col==cols-1 else 1.0
            bottom_penalty=0.78 if row>=rows-1 else 1.0
            score=(blank*right_weight*center_weight*vertical_weight+row_deficit*0.38+col_deficit*0.72)*edge_penalty*bottom_penalty
            if score>0.28:
                scored.append((score,row,col))
    scored.sort(reverse=True)
    return [(row,col) for _,row,col in scored[:(limit or RIGHT_CENTER_VOID_RELOCATE_TARGETS)]]

def right_center_void_relocate(pl, rounds=1):
    if not (LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE and LOW_ALPHA_READABLE_POSTPROCESS and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    global RIGHT_CENTER_VOID_RELOCATE_APPLIED, RIGHT_CENTER_VOID_RELOCATE_MOVES, RIGHT_CENTER_VOID_RELOCATE_GAIN
    global RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE, RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER
    global RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE, RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER
    base_alpha=material_alpha_topup_alpha(pl)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_metrics=right_center_void_metrics(base_audit)
    RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE=base_metrics["right_blank"]
    RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER=base_metrics["right_blank"]
    RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE=base_metrics["mid_right_blank"]
    RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER=base_metrics["mid_right_blank"]
    base_stats=orientation_stats(pl)
    if base_stats["readable"]<N or base_stats["upside"]>0 or base_stats["sideways"]>0 or base_stats["hard"]>0:
        return pl
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    best_trial=None
    node_count=0
    trial_count=0
    debug_best=None
    scale_factors=(1.018,1.012,1.006,1.0,0.996,0.992)

    for _ in range(max(1,rounds)):
        current_audit=visual_audit_like(current)
        for row,col in right_center_void_targets(current_audit,RIGHT_CENTER_VOID_RELOCATE_TARGETS):
            if node_count>RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT:
                break
            cx=(col+0.5)*SW/8
            cy=(row+0.5)*SH/10
            donors=band_void_fill_donors(current,current_audit,cx,cy,RIGHT_CENTER_VOID_RELOCATE_DONORS)
            for pos in donors:
                if node_count>RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT:
                    break
                i,x,y,r,s=current[pos]
                fixed=build_occ_except_positions(current,{pos})
                old_m=make(i,r,s,gap=True)
                old_cx=x+old_m.shape[1]/2
                old_cy=y+old_m.shape[0]/2
                donor_row=min(9,max(0,int(old_cy*10/max(1,SH))))
                wall=dil(fixed,1)&(~fixed)
                options=[]
                for factor in scale_factors:
                    ns=round(clamp_scale(i,s*factor),4)
                    if ns<s-0.008:
                        continue
                    if abs(ns-s)<0.0001 and abs(factor-1.0)>0.0001:
                        continue
                    m=make(i,r,ns,gap=True)
                    h,w=m.shape
                    if h>SH or w>SW:
                        continue
                    desired_x=int(round(cx-w/2))
                    desired_y=int(round(cy-h/2))
                    candidates=set()
                    guided=place_guided(fixed,m,desired_x,desired_y,row_strength=1.95)
                    node_count+=1
                    if guided is not None:
                        candidates.add(guided)
                    for radius in (0,4,8,12,18,24):
                        step=max(4,radius or 4)
                        for dy in range(-radius,radius+1,step):
                            for dx in range(-radius,radius+1,step):
                                if radius and abs(dx)!=radius and abs(dy)!=radius:
                                    continue
                                xx=min(max(0,desired_x+dx),SW-w)
                                yy=min(max(0,desired_y+dy),SH-h)
                                candidates.add((xx,yy))
                    for xx,yy in candidates:
                        node_count+=1
                        if node_count>RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT:
                            break
                        if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                            continue
                        region=fixed[yy:yy+h,xx:xx+w]
                        if region.shape!=m.shape or (region&m).any():
                            continue
                        contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum())) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
                        move=abs((xx+w/2)-old_cx)+abs((yy+h/2)-old_cy)
                        target_dist=abs((xx+w/2)-cx)+abs((yy+h/2)-cy)
                        grow=max(0.0,ns-s)
                        score=grow*max(1,int(make(i,r,s,gap=False).sum()))*0.30+contact*66.0-target_dist*0.024-move*0.012
                        options.append((score,xx,yy,ns))
                    if node_count>RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT:
                        break
                for _,nx,ny,ns in sorted(options,reverse=True)[:RIGHT_CENTER_VOID_RELOCATE_OPTIONS]:
                    trial=current[:]
                    trial[pos]=(i,nx,ny,r,ns)
                    if layout_overlap_cells(trial)>0:
                        continue
                    trial_count+=1
                    trial_stats=orientation_stats(trial)
                    if trial_stats["readable"]<N or trial_stats["upside"]>0 or trial_stats["sideways"]>0 or trial_stats["hard"]>0:
                        continue
                    if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                        continue
                    trial_alpha=material_alpha_topup_alpha(trial)
                    if trial_alpha<base_alpha-0.00020:
                        continue
                    trial_audit=visual_audit_like(trial)
                    trial_metrics=right_center_void_metrics(trial_audit)
                    right_gain=base_metrics["right_blank"]-trial_metrics["right_blank"]
                    mid_right_gain=base_metrics["mid_right_blank"]-trial_metrics["mid_right_blank"]
                    center_gain=base_audit["center_blank"]-trial_audit["center_blank"]
                    lower_gain=base_audit["lower_blank"]-trial_audit["lower_blank"]
                    target_tile_gain=trial_audit["tile_fills"][row*8+col]-base_audit["tile_fills"][row*8+col]
                    donor_row_loss=base_audit["row_fills"][donor_row]-trial_audit["row_fills"][donor_row]
                    void_gain=max(0.0,right_gain)*1.35+max(0.0,mid_right_gain)+max(0.0,center_gain)*0.42+max(0.0,lower_gain)*0.20+max(0.0,target_tile_gain)*0.70
                    if RECOVERY_DEBUG:
                        near_score=(trial_alpha-base_alpha)*950.0+void_gain*7.0+(trial_audit["selection"]-base_audit["selection"])*0.000001-donor_row_loss*1.8
                        if debug_best is None or near_score>debug_best[0]:
                            debug_best=(near_score,trial_alpha,void_gain,right_gain,mid_right_gain,center_gain,lower_gain,target_tile_gain,donor_row_loss,trial_audit["score"],trial_audit["large_blank"],trial_audit["size_cv"])
                    if void_gain<RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN and target_tile_gain<0.014:
                        continue
                    if right_gain<0.0010 and mid_right_gain<0.0010 and target_tile_gain<0.018:
                        continue
                    if donor_row_loss>0.024:
                        continue
                    if trial_audit["score"]<base_audit["score"]-2:
                        continue
                    if trial_audit["large_blank"]>base_audit["large_blank"]+0.006:
                        continue
                    if trial_audit["center_blank"]>base_audit["center_blank"]+0.004:
                        continue
                    if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.004:
                        continue
                    if trial_audit["layout_bbox"]>base_audit["layout_bbox"]+0.010:
                        continue
                    if trial_audit["size_cv"]>base_cv+0.008:
                        continue
                    if layout_quality(trial)<base_quality-0.080:
                        continue
                    move=abs((nx+make(i,r,ns,gap=True).shape[1]/2)-old_cx)+abs((ny+make(i,r,ns,gap=True).shape[0]/2)-old_cy)
                    score=(trial_alpha-base_alpha)*120000.0+void_gain*5200.0+target_tile_gain*2500.0+(trial_audit["selection"]-base_audit["selection"])*0.0010-donor_row_loss*850.0-move*0.014
                    if best_trial is None or score>best_trial[0]:
                        best_trial=(score,trial,trial_alpha,void_gain,trial_metrics)
                if node_count>RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT:
                    break
            if best_trial is not None:
                break
        if best_trial is not None:
            break

    if best_trial is not None:
        _,trial,best_alpha,best_gain,trial_metrics=best_trial
        RIGHT_CENTER_VOID_RELOCATE_APPLIED=True
        RIGHT_CENTER_VOID_RELOCATE_MOVES=1
        RIGHT_CENTER_VOID_RELOCATE_GAIN=best_gain
        RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER=trial_metrics["right_blank"]
        RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER=trial_metrics["mid_right_blank"]
        if RECOVERY_DEBUG:
            after=visual_audit_like(trial)
            print(f"right_center_void_relocate accepted moves=1 alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{after['score']} rightBlank={base_metrics['right_blank']:.3f}->{trial_metrics['right_blank']:.3f} midRightBlank={base_metrics['mid_right_blank']:.3f}->{trial_metrics['mid_right_blank']:.3f} gain={best_gain:.4f} node_count={node_count}", file=sys.stderr)
        return trial
    if RECOVERY_DEBUG and LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE:
        if debug_best is not None:
            _,dbg_alpha,dbg_gain,dbg_right,dbg_mid,dbg_center,dbg_lower,dbg_tile,dbg_row_loss,dbg_score,dbg_large,dbg_cv=debug_best
            print(f"right_center_void_relocate rejected base_alpha={base_alpha*100:.3f}% minVoid={RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count} best_alpha={dbg_alpha*100:.3f}% best_gain={dbg_gain:.4f} right_gain={dbg_right:.4f} mid_right_gain={dbg_mid:.4f} center_gain={dbg_center:.4f} lower_gain={dbg_lower:.4f} target_tile_gain={dbg_tile:.4f} donor_row_loss={dbg_row_loss:.4f} best_visual={dbg_score} best_large={dbg_large:.4f} best_cv={dbg_cv:.4f}", file=sys.stderr)
        else:
            print(f"right_center_void_relocate rejected base_alpha={base_alpha*100:.3f}% minVoid={RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count}", file=sys.stderr)
    return pl

def right_center_void_chain_relocate(pl, rounds=1):
    if not (LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE and LOW_ALPHA_READABLE_POSTPROCESS and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED, RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED, RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MOVES
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN, RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN, RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN
    global RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_BEFORE, RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER
    global RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_BEFORE, RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER
    base_alpha=material_alpha_topup_alpha(pl)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_metrics=right_center_void_metrics(base_audit)
    RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_BEFORE=base_metrics["right_blank"]
    RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER=base_metrics["right_blank"]
    RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_BEFORE=base_metrics["mid_right_blank"]
    RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER=base_metrics["mid_right_blank"]
    base_stats=orientation_stats(pl)
    if base_stats["readable"]<N or base_stats["upside"]>0 or base_stats["sideways"]>0 or base_stats["hard"]>0:
        return pl
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    best_trial=None
    best_two_step_score=None
    best_two_step_alpha=None
    best_two_step_void_gain=None
    node_count=0
    trial_count=0
    debug_best=None
    mover_factors=(1.024,1.018,1.012,1.006,1.0)
    backfill_factors=(1.012,1.006,1.0,0.996)

    def guided_options(layout, pos, fixed, target_cx, target_cy, factors, row_strength, limit, node_cap=None):
        nonlocal node_count
        cap=node_cap if node_cap is not None else RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT
        i,x,y,r,s=layout[pos]
        old_m=make(i,r,s,gap=True)
        old_cx=x+old_m.shape[1]/2
        old_cy=y+old_m.shape[0]/2
        wall=dil(fixed,1)&(~fixed)
        options=[]
        for factor in factors:
            ns=round(clamp_scale(i,s*factor),4)
            if ns<s-0.006:
                continue
            if abs(ns-s)<0.0001 and abs(factor-1.0)>0.0001:
                continue
            m=make(i,r,ns,gap=True)
            h,w=m.shape
            if h>SH or w>SW:
                continue
            desired_x=int(round(target_cx-w/2))
            desired_y=int(round(target_cy-h/2))
            candidates=set()
            if node_count>=cap:
                break
            guided=place_guided(fixed,m,desired_x,desired_y,row_strength=row_strength)
            node_count+=1
            if guided is not None:
                candidates.add(guided)
            for radius in (0,4,8,12,18,24):
                step=max(4,radius or 4)
                for dy in range(-radius,radius+1,step):
                    for dx in range(-radius,radius+1,step):
                        if radius and abs(dx)!=radius and abs(dy)!=radius:
                            continue
                        xx=min(max(0,desired_x+dx),SW-w)
                        yy=min(max(0,desired_y+dy),SH-h)
                        candidates.add((xx,yy))
            for xx,yy in candidates:
                if node_count>=cap:
                    break
                node_count+=1
                if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                    continue
                region=fixed[yy:yy+h,xx:xx+w]
                if region.shape!=m.shape or (region&m).any():
                    continue
                contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum())) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
                move=abs((xx+w/2)-old_cx)+abs((yy+h/2)-old_cy)
                target_dist=abs((xx+w/2)-target_cx)+abs((yy+h/2)-target_cy)
                grow=max(0.0,ns-s)
                score=grow*max(1,int(make(i,r,s,gap=False).sum()))*0.32+contact*68.0-target_dist*0.026-move*0.011
                options.append((score,xx,yy,ns))
            if node_count>=cap:
                break
        return sorted(options,reverse=True)[:limit]

    def consider_chain_trial(trial, changed, row, col, donor_row, move_penalty, second_backfill_used=False, second_row=None, second_col=None):
        nonlocal best_trial, best_two_step_score, best_two_step_alpha, best_two_step_void_gain, trial_count, debug_best
        if changed<2:
            return
        if layout_overlap_cells(trial)>0:
            return
        trial_count+=1
        trial_stats=orientation_stats(trial)
        if trial_stats["readable"]<N or trial_stats["upside"]>0 or trial_stats["sideways"]>0 or trial_stats["hard"]>0:
            return
        if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
            return
        trial_alpha=material_alpha_topup_alpha(trial)
        if trial_alpha<base_alpha+RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN:
            return
        trial_audit=visual_audit_like(trial)
        trial_metrics=right_center_void_metrics(trial_audit)
        right_gain=base_metrics["right_blank"]-trial_metrics["right_blank"]
        mid_right_gain=base_metrics["mid_right_blank"]-trial_metrics["mid_right_blank"]
        center_gain=base_audit["center_blank"]-trial_audit["center_blank"]
        lower_gain=base_audit["lower_blank"]-trial_audit["lower_blank"]
        target_tile_gain=trial_audit["tile_fills"][row*8+col]-base_audit["tile_fills"][row*8+col]
        second_target_tile_gain=0.0
        if second_row is not None and second_col is not None:
            second_target_tile_gain=trial_audit["tile_fills"][second_row*8+second_col]-base_audit["tile_fills"][second_row*8+second_col]
        donor_row_loss=base_audit["row_fills"][donor_row]-trial_audit["row_fills"][donor_row]
        target_tile_bonus=max(0.0,target_tile_gain,second_target_tile_gain)
        void_gain=max(0.0,right_gain)*1.35+max(0.0,mid_right_gain)+max(0.0,center_gain)*0.42+max(0.0,lower_gain)*0.20+target_tile_bonus*0.70
        if RECOVERY_DEBUG:
            near_score=(trial_alpha-base_alpha)*1500.0+void_gain*8.0+target_tile_gain*3.0-donor_row_loss*2.2+(trial_audit["selection"]-base_audit["selection"])*0.000001
            if debug_best is None or near_score>debug_best[0]:
                debug_best=(near_score,trial_alpha,void_gain,right_gain,mid_right_gain,center_gain,lower_gain,target_tile_gain,donor_row_loss,trial_audit["score"],trial_audit["large_blank"],trial_audit["size_cv"])
        if void_gain<RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN:
            return
        if right_gain<0.0010 and mid_right_gain<0.0010 and target_tile_bonus<0.014:
            return
        if donor_row_loss>0.026:
            return
        if trial_audit["row_imbalance"]>base_audit["row_imbalance"]+0.030:
            return
        if trial_audit["score"]<base_audit["score"]-2:
            return
        if trial_audit["large_blank"]>base_audit["large_blank"]+0.006:
            return
        if trial_audit["center_blank"]>base_audit["center_blank"]+0.003:
            return
        if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.003:
            return
        if trial_audit["layout_bbox"]>base_audit["layout_bbox"]+0.010:
            return
        if trial_audit["size_cv"]>base_cv+0.008:
            return
        if layout_quality(trial)<base_quality-0.080:
            return
        score=(trial_alpha-base_alpha)*160000.0+void_gain*5600.0+target_tile_bonus*3000.0+(trial_audit["selection"]-base_audit["selection"])*0.0010-donor_row_loss*900.0-move_penalty*0.011
        second_extra_alpha_gain=0.0
        second_extra_void_gain=0.0
        if second_backfill_used and best_two_step_alpha is not None:
            second_extra_alpha_gain=trial_alpha-best_two_step_alpha
            second_extra_void_gain=void_gain-best_two_step_void_gain
            if second_extra_alpha_gain<RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN and second_extra_void_gain<RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN:
                return
        if second_backfill_used and best_two_step_alpha is None:
            return
        if not second_backfill_used and (best_two_step_score is None or score>best_two_step_score):
            best_two_step_score=score
            best_two_step_alpha=trial_alpha
            best_two_step_void_gain=void_gain
        if second_backfill_used:
            score+=220.0
        if best_trial is None or score>best_trial[0]:
            best_trial=(score,trial,trial_alpha,void_gain,trial_metrics,changed,second_backfill_used,second_extra_alpha_gain,second_extra_void_gain)

    for _ in range(max(1,rounds)):
        current_audit=visual_audit_like(current)
        for row,col in right_center_void_targets(current_audit,RIGHT_CENTER_VOID_CHAIN_RELOCATE_TARGETS):
            if node_count>RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT:
                break
            target_cx=(col+0.5)*SW/8
            target_cy=(row+0.5)*SH/10
            donors=band_void_fill_donors(current,current_audit,target_cx,target_cy,RIGHT_CENTER_VOID_CHAIN_RELOCATE_DONORS)
            for mover in donors:
                if node_count>RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT:
                    break
                mi,mx,my,mr,ms=current[mover]
                old_m=make(mi,mr,ms,gap=True)
                old_cx=mx+old_m.shape[1]/2
                old_cy=my+old_m.shape[0]/2
                donor_row=min(9,max(0,int(old_cy*10/max(1,SH))))
                backfills=band_void_fill_backfills(current,current_audit,mover,old_cx,old_cy,RIGHT_CENTER_VOID_CHAIN_RELOCATE_BACKFILLS)
                for backfill in backfills:
                    if node_count>RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT:
                        break
                    fixed=build_occ_except_positions(current,{mover,backfill})
                    mover_options=guided_options(current,mover,fixed,target_cx,target_cy,mover_factors,2.20,min(10,RIGHT_CENTER_VOID_CHAIN_RELOCATE_OPTIONS))
                    for _,nx,ny,ns in mover_options:
                        if node_count>RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT:
                            break
                        mover_mask=make(mi,mr,ns,gap=True)
                        occ=fixed.copy()
                        stamp(occ,nx,ny,mover_mask)
                        backfill_options=guided_options(current,backfill,occ,old_cx,old_cy,backfill_factors,1.85,min(8,RIGHT_CENTER_VOID_CHAIN_RELOCATE_OPTIONS))
                        bi,bx,by,br,bs=current[backfill]
                        old_backfill=make(bi,br,bs,gap=True)
                        old_backfill_cx=bx+old_backfill.shape[1]/2
                        old_backfill_cy=by+old_backfill.shape[0]/2
                        for _,bxx,byy,bns in backfill_options:
                            trial=current[:]
                            trial[mover]=(mi,nx,ny,mr,ns)
                            trial[backfill]=(bi,bxx,byy,br,bns)
                            changed=0
                            if nx!=mx or ny!=my or abs(ns-ms)>0.0001:
                                changed+=1
                            if bxx!=bx or byy!=by or abs(bns-bs)>0.0001:
                                changed+=1
                            mover_move=abs((nx+make(mi,mr,ns,gap=True).shape[1]/2)-old_cx)+abs((ny+make(mi,mr,ns,gap=True).shape[0]/2)-old_cy)
                            backfill_move=abs((bxx+make(bi,br,bns,gap=True).shape[1]/2)-old_backfill_cx)+abs((byy+make(bi,br,bns,gap=True).shape[0]/2)-old_backfill_cy)
                            consider_chain_trial(trial,changed,row,col,donor_row,mover_move+backfill_move,False)
                            if LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and best_trial is not None:
                                second_node_cap=min(RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT,node_count+3500)
                                second_target_specs=[]
                                if RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET:
                                    trial_audit_for_second=visual_audit_like(trial)
                                    second_target_cells=right_center_void_targets(trial_audit_for_second,min(2,RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS))
                                    second_target_cells+=band_void_fill_targets(trial_audit_for_second,1)
                                    seen_second_targets=set()
                                    for second_row,second_col in second_target_cells:
                                        if (second_row,second_col) in seen_second_targets:
                                            continue
                                        seen_second_targets.add((second_row,second_col))
                                        second_target_cx=(second_col+0.5)*SW/8
                                        second_target_cy=(second_row+0.5)*SH/10
                                        second_donors=band_void_fill_donors(current,trial_audit_for_second,second_target_cx,second_target_cy,RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS)
                                        second_target_specs.append((second_row,second_col,second_target_cx,second_target_cy,second_donors))
                                else:
                                    second_backfills=band_void_fill_backfills(current,current_audit,backfill,old_backfill_cx,old_backfill_cy,RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS)
                                    second_target_specs.append((None,None,old_backfill_cx,old_backfill_cy,second_backfills))
                                for second_row,second_col,second_target_cx,second_target_cy,second_donors in second_target_specs:
                                    if node_count>second_node_cap:
                                        break
                                    for second_backfill in second_donors:
                                        if node_count>second_node_cap:
                                            break
                                        if second_backfill in (mover,backfill):
                                            continue
                                        fixed2=build_occ_except_positions(current,{mover,backfill,second_backfill})
                                        occ2=fixed2.copy()
                                        stamp(occ2,nx,ny,make(mi,mr,ns,gap=True))
                                        stamp(occ2,bxx,byy,make(bi,br,bns,gap=True))
                                        second_options=guided_options(current,second_backfill,occ2,second_target_cx,second_target_cy,(1.012,1.006,1.0,0.996),1.75,min(5,RIGHT_CENTER_VOID_CHAIN_RELOCATE_OPTIONS),second_node_cap)
                                        si,sx,sy,sr,ss=current[second_backfill]
                                        old_second=make(si,sr,ss,gap=True)
                                        old_second_cx=sx+old_second.shape[1]/2
                                        old_second_cy=sy+old_second.shape[0]/2
                                        for _,sxx,syy,sns in second_options:
                                            trial2=trial[:]
                                            trial2[second_backfill]=(si,sxx,syy,sr,sns)
                                            changed2=changed
                                            if sxx!=sx or syy!=sy or abs(sns-ss)>0.0001:
                                                changed2+=1
                                            if changed2<3:
                                                continue
                                            second_move=abs((sxx+make(si,sr,sns,gap=True).shape[1]/2)-old_second_cx)+abs((syy+make(si,sr,sns,gap=True).shape[0]/2)-old_second_cy)
                                            consider_chain_trial(trial2,changed2,row,col,donor_row,mover_move+backfill_move+second_move,True,second_row,second_col)
                if best_trial is not None and (not (LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET) or best_trial[6]):
                    break
            if best_trial is not None and (not (LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET) or best_trial[6]):
                break
        if best_trial is not None and (not (LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET) or best_trial[6]):
            break

    if best_trial is not None:
        _,trial,best_alpha,best_gain,trial_metrics,best_move_count,second_backfill_used,second_extra_alpha_gain,second_extra_void_gain=best_trial
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED=True
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED=bool(second_backfill_used)
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MOVES=best_move_count if second_backfill_used else 0
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN=second_extra_alpha_gain if second_backfill_used else 0.0
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN=second_extra_void_gain if second_backfill_used else 0.0
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES=best_move_count
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN=max(0.0,best_alpha-base_alpha)
        RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN=best_gain
        RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER=trial_metrics["right_blank"]
        RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER=trial_metrics["mid_right_blank"]
        if RECOVERY_DEBUG:
            after=visual_audit_like(trial)
            print(f"right_center_void_chain_relocate accepted moves={best_move_count} secondBackfill={RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{after['score']} rightBlank={base_metrics['right_blank']:.3f}->{trial_metrics['right_blank']:.3f} midRightBlank={base_metrics['mid_right_blank']:.3f}->{trial_metrics['mid_right_blank']:.3f} alpha_gain={RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN:.4f} void_gain={best_gain:.4f} secondExtraAlpha={RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN:.4f} secondExtraVoid={RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN:.4f} node_count={node_count} trials={trial_count}", file=sys.stderr)
        return trial
    if RECOVERY_DEBUG and LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE:
        if debug_best is not None:
            _,dbg_alpha,dbg_gain,dbg_right,dbg_mid,dbg_center,dbg_lower,dbg_tile,dbg_row_loss,dbg_score,dbg_large,dbg_cv=debug_best
            print(f"right_center_void_chain_relocate rejected base_alpha={base_alpha*100:.3f}% minAlpha={RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN:.4f} minVoid={RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count} best_alpha={dbg_alpha*100:.3f}% best_gain={dbg_gain:.4f} right_gain={dbg_right:.4f} mid_right_gain={dbg_mid:.4f} center_gain={dbg_center:.4f} lower_gain={dbg_lower:.4f} target_tile_gain={dbg_tile:.4f} donor_row_loss={dbg_row_loss:.4f} best_visual={dbg_score} best_large={dbg_large:.4f} best_cv={dbg_cv:.4f}", file=sys.stderr)
        else:
            print(f"right_center_void_chain_relocate rejected base_alpha={base_alpha*100:.3f}% minAlpha={RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN:.4f} minVoid={RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN:.4f} node_count={node_count} trials={trial_count}", file=sys.stderr)
    return pl

def band_void_fill_relocate(pl, rounds=1):
    if not (LOW_ALPHA_READABLE_BAND_VOID_FILL and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER and pl):
        return pl
    if not material_alpha_topup_seed_allowed() or len(pl)!=N:
        return pl
    base_alpha=material_alpha_topup_alpha(pl)
    accept_threshold=max(BAND_VOID_FILL_MIN_ACCEPT,base_alpha+BAND_VOID_FILL_MIN_GAIN)
    base_audit=visual_audit_like(pl)
    if base_audit["score"]<MATERIAL_ALPHA_TOPUP_MIN_VISUAL_SCORE:
        return pl
    base_stats=orientation_stats(pl)
    base_quality=layout_quality(pl)
    base_cv=base_audit["size_cv"]
    current=pl[:]
    best_trial=None
    best_alpha=base_alpha
    best_move_count=0
    node_count=0
    trial_count=0
    debug_best=None
    scale_factors=(1.024,1.018,1.012,1.006,1.0,0.994)

    for _ in range(max(1,rounds)):
        current_audit=visual_audit_like(current)
        for row,col in band_void_fill_targets(current_audit,BAND_VOID_FILL_TARGETS):
            if node_count>BAND_VOID_FILL_NODE_LIMIT:
                break
            cx=(col+0.5)*SW/8
            cy=(row+0.5)*SH/10
            donors=band_void_fill_donors(current,current_audit,cx,cy,BAND_VOID_FILL_DONORS)
            for pos in donors:
                if node_count>BAND_VOID_FILL_NODE_LIMIT:
                    break
                i,x,y,r,s=current[pos]
                fixed=build_occ_except_positions(current,{pos})
                old_m=make(i,r,s,gap=True)
                old_cx=x+old_m.shape[1]/2
                old_cy=y+old_m.shape[0]/2
                wall=dil(fixed,1)&(~fixed)
                options=[]
                for factor in scale_factors:
                    ns=round(clamp_scale(i,s*factor),4)
                    if ns<s-0.006:
                        continue
                    if abs(ns-s)<0.0001 and abs(factor-1.0)>0.0001:
                        continue
                    m=make(i,r,ns,gap=True)
                    h,w=m.shape
                    if h>SH or w>SW:
                        continue
                    desired_x=int(round(cx-w/2))
                    desired_y=int(round(cy-h/2))
                    candidates=set()
                    guided=place_guided(fixed,m,desired_x,desired_y,row_strength=2.10)
                    node_count+=1
                    if guided is not None:
                        candidates.add(guided)
                    for radius in (0,4,8,12,18):
                        step=max(4,radius or 4)
                        for dy in range(-radius,radius+1,step):
                            for dx in range(-radius,radius+1,step):
                                if radius and abs(dx)!=radius and abs(dy)!=radius:
                                    continue
                                xx=min(max(0,desired_x+dx),SW-w)
                                yy=min(max(0,desired_y+dy),SH-h)
                                candidates.add((xx,yy))
                    for xx,yy in candidates:
                        node_count+=1
                        if node_count>BAND_VOID_FILL_NODE_LIMIT:
                            break
                        if xx<0 or yy<0 or xx+w>SW or yy+h>SH:
                            continue
                        region=fixed[yy:yy+h,xx:xx+w]
                        if region.shape!=m.shape or (region&m).any():
                            continue
                        contact=float((wall[yy:yy+h,xx:xx+w]&m).sum())/max(1,int(m.sum())) if wall[yy:yy+h,xx:xx+w].shape==m.shape else 0.0
                        move=abs((xx+w/2)-old_cx)+abs((yy+h/2)-old_cy)
                        target_dist=abs((xx+w/2)-cx)+abs((yy+h/2)-cy)
                        grow=max(0.0,ns-s)
                        score=grow*max(1,int(make(i,r,s,gap=False).sum()))*0.34+contact*70.0-move*0.012-target_dist*0.020
                        options.append((score,xx,yy,ns))
                    if node_count>BAND_VOID_FILL_NODE_LIMIT:
                        break
                for _,nx,ny,ns in sorted(options,reverse=True)[:BAND_VOID_FILL_OPTIONS]:
                    trial=current[:]
                    trial[pos]=(i,nx,ny,r,ns)
                    if layout_overlap_cells(trial)>0:
                        continue
                    trial_count+=1
                    trial_stats=orientation_stats(trial)
                    if trial_stats["readable"]<base_stats["readable"] or trial_stats["upside"]>base_stats["upside"] or trial_stats["sideways"]>base_stats["sideways"] or trial_stats["hard"]>base_stats["hard"]:
                        continue
                    trial_alpha=material_alpha_topup_alpha(trial)
                    trial_audit=visual_audit_like(trial)
                    center_gain=base_audit["center_blank"]-trial_audit["center_blank"]
                    lower_gain=base_audit["lower_blank"]-trial_audit["lower_blank"]
                    void_gain=max(0.0,center_gain)+max(0.0,lower_gain)*1.25
                    if RECOVERY_DEBUG:
                        near_score=(trial_alpha-base_alpha)*1000.0+void_gain*4.0+(trial_audit["selection"]-base_audit["selection"])*0.000001
                        if debug_best is None or near_score>debug_best[0]:
                            debug_best=(near_score,trial_alpha,void_gain,center_gain,lower_gain,trial_audit["score"],trial_audit["large_blank"],trial_audit["size_cv"])
                    material_gain_ok=trial_alpha>=accept_threshold-1e-6 and trial_alpha>best_alpha+0.00001
                    visual_void_ok=trial_alpha>=base_alpha-0.00030 and (
                        void_gain>=0.006
                        or center_gain>=0.004
                        or lower_gain>=0.004
                        or trial_audit["selection"]>=base_audit["selection"]+700
                    )
                    if not (material_gain_ok or visual_void_ok):
                        continue
                    if trial_audit["score"]<base_audit["score"]-2:
                        continue
                    if trial_audit["large_blank"]>base_audit["large_blank"]+0.006:
                        continue
                    if trial_audit["center_blank"]>base_audit["center_blank"]+0.004:
                        continue
                    if trial_audit["lower_blank"]>base_audit["lower_blank"]+0.004:
                        continue
                    if trial_audit["size_cv"]>base_cv+0.008:
                        continue
                    trial_quality=layout_quality(trial)
                    if trial_quality<base_quality-0.080:
                        continue
                    move=abs((nx+make(i,r,ns,gap=True).shape[1]/2)-old_cx)+abs((ny+make(i,r,ns,gap=True).shape[0]/2)-old_cy)
                    score=(trial_alpha-base_alpha)*130000.0+void_gain*2200.0+(trial_audit["selection"]-base_audit["selection"])*0.0010-move*0.018
                    if best_trial is None or score>best_trial[0]:
                        best_trial=(score,trial,trial_alpha,1)
                if node_count>BAND_VOID_FILL_NODE_LIMIT:
                    break
            if best_trial is not None:
                break
        if best_trial is not None:
            break

    if best_trial is not None:
        _,trial,best_alpha,best_move_count=best_trial
        global BAND_VOID_FILL_APPLIED, BAND_VOID_FILL_MOVES
        BAND_VOID_FILL_APPLIED=True
        BAND_VOID_FILL_MOVES=best_move_count
        if RECOVERY_DEBUG:
            after=visual_audit_like(trial)
            print(f"band_void_fill accepted moves={best_move_count} alpha={base_alpha*100:.3f}->{best_alpha*100:.3f}% visual={base_audit['score']}->{after['score']} centerBlank={base_audit['center_blank']:.3f}->{after['center_blank']:.3f} lowerBlank={base_audit['lower_blank']:.3f}->{after['lower_blank']:.3f} node_count={node_count}", file=sys.stderr)
        return trial
    if RECOVERY_DEBUG and LOW_ALPHA_READABLE_BAND_VOID_FILL:
        if debug_best is not None:
            _,dbg_alpha,dbg_void,dbg_center,dbg_lower,dbg_score,dbg_large,dbg_cv=debug_best
            print(f"band_void_fill rejected base_alpha={base_alpha*100:.3f}% accept={accept_threshold*100:.3f}% node_count={node_count} trials={trial_count} best_alpha={dbg_alpha*100:.3f}% best_void_gain={dbg_void:.4f} center_gain={dbg_center:.4f} lower_gain={dbg_lower:.4f} best_visual={dbg_score} best_large={dbg_large:.4f} best_cv={dbg_cv:.4f}", file=sys.stderr)
        else:
            print(f"band_void_fill rejected base_alpha={base_alpha*100:.3f}% accept={accept_threshold*100:.3f}% node_count={node_count} trials={trial_count}", file=sys.stderr)
    return pl

def void_relocate(pl, rounds=1):
    if not VOID_RELOCATE:
        return pl
    pl=pl[:]
    best_q=layout_quality(pl);best_alpha=ink(pl)
    for _ in range(rounds):
        moved=False
        targets=sparse_targets(pl,limit=5)
        if not targets:
            break
        # Small and medium stickers are best for filling visual holes without
        # creating another equally large hole where they came from.
        candidate_order=sorted(range(len(pl)), key=lambda k:make(pl[k][0],pl[k][3],pl[k][4],gap=False).sum())[:10]
        for _,_,cx,cy,_,_ in targets:
            for k in candidate_order:
                i,x,y,r,s=pl[k]
                current_m=make(i,r,s,gap=True)
                old_cx=x+current_m.shape[1]/2;old_cy=y+current_m.shape[0]/2
                if abs(old_cx-cx)+abs(old_cy-cy)<max(SW,SH)*0.10:
                    continue
                base=[entry for j,entry in enumerate(pl) if j!=k]
                occ=BASE_OCC.copy()
                for ii,xx,yy,rr,ss in base:
                    mm=make(ii,rr,ss,gap=True);stamp(occ,xx,yy,mm)
                variants=[]
                for rr in local_angle_candidates(r,broad=MANUAL_STAGGER):
                    for ss in [s,clamp_scale(i,s*0.99),clamp_scale(i,s*0.975),clamp_scale(i,s*1.01)]:
                        pair=(rr,round(ss,4))
                        if pair not in variants:
                            variants.append(pair)
                for rr,ss in variants[:18 if MANUAL_STAGGER else 8]:
                    mm=make(i,rr,ss,gap=True)
                    p=place_guided(occ,mm,cx-mm.shape[1]/2,cy-mm.shape[0]/2,row_strength=1.55)
                    if p is None:
                        continue
                    trial=base+[(i,p[0],p[1],rr,ss)]
                    q=layout_quality(trial);a=ink(trial)
                    if (q>best_q+0.012 and a>=best_alpha-0.0025) or a>best_alpha+0.004:
                        pl=compact(trial,rounds=1);best_q=max(best_q,layout_quality(pl));best_alpha=max(best_alpha,ink(pl));moved=True
                        break
                if moved:
                    break
            if moved:
                break
        if not moved:
            break
    return pl

def upside_rescue_refit(pl, rounds=2):
    if not (UPSIDE_RESCUE_REFIT and READABILITY_GUARD and MANUAL_STAGGER) or not pl:
        return pl
    original_stats=orientation_stats(pl)
    if original_stats["upside_ratio"]<=MAX_UPSIDE_RATIO:
        return pl
    original_alpha=ink(pl)
    min_rescue_alpha=max(UPSIDE_RESCUE_MIN_ALPHA, original_alpha-UPSIDE_RESCUE_MAX_ALPHA_LOSS)
    original_quality=layout_quality(pl)
    current=pl[:]
    current_stats=original_stats
    readable_angles=[0,8,352,12,348,15,345,30,330]
    for _ in range(rounds):
        improved=False
        upside_indices=[
            k for k,entry in enumerate(current)
            if orientation_bucket(entry[3])=="upside"
        ]
        # Try smaller/easier masks first. They are more likely to turn upright
        # near the current cavity without breaking the already solved 25/25 fit.
        upside_indices.sort(key=lambda k:make(current[k][0],current[k][3],current[k][4],gap=False).sum())
        for k in upside_indices:
            i,x,y,r,s=current[k]
            old_mask=make(i,r,s,gap=True)
            cx=x+old_mask.shape[1]/2
            cy=y+old_mask.shape[0]/2
            base=[entry for j,entry in enumerate(current) if j!=k]
            occ=BASE_OCC.copy()
            for ii,xx,yy,rr,ss in base:
                stamp(occ,xx,yy,make(ii,rr,ss,gap=True))
            best_trial=None
            best_score=-1e18
            scale_options=uniq([round(clamp_scale(i,s*f),4) for f in [1.0,0.99,0.98,0.965]])
            for rr in readable_angles:
                for ss in scale_options:
                    mm=make(i,rr,ss,gap=True)
                    p=place_near(occ,mm,cx,cy,radius_cells=48)
                    if p is None:
                        continue
                    trial=base+[(i,p[0],p[1],rr,ss)]
                    if len(trial)!=N or orientation_hard_reject(trial):
                        continue
                    stats=orientation_stats(trial)
                    if stats["upside"]>=current_stats["upside"]:
                        continue
                    a=ink(trial)
                    if a < min_rescue_alpha:
                        continue
                    q=layout_quality(trial)
                    if q < original_quality-0.18:
                        continue
                    score=(current_stats["upside"]-stats["upside"])*0.70
                    score+=(stats["readable"]-current_stats["readable"])*0.18
                    score+=(a-original_alpha)*10.0
                    score+=(q-original_quality)*0.35
                    if score>best_score:
                        best_trial=trial
                        best_score=score
            if best_trial is not None:
                current=best_trial
                current_stats=orientation_stats(current)
                improved=True
                if current_stats["upside_ratio"]<=MAX_UPSIDE_RATIO:
                    return current
                break
        if not improved:
            break
    return current

def metadata_bool(value):
    if isinstance(value,bool):
        return value
    if isinstance(value,(int,float)):
        return value!=0
    if isinstance(value,str):
        return value.strip().lower() in ("1","true","yes","on")
    return False

def metadata_int(value, default=0):
    try:
        return int(round(float(value)))
    except Exception:
        return default

def metadata_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def refresh_right_center_void_chain_carryforward():
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED, RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN, RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED=bool(RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED or RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED)
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES=int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES)+int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_MOVES)
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN=max(0.0,float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN))+max(0.0,float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_ALPHA_GAIN))
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN=max(0.0,float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN),float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_VOID_GAIN))

def load_polish_base_layout(path):
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED, RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_MOVES
    global RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_ALPHA_GAIN, RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_VOID_GAIN
    try:
        with open(path,"r",encoding="utf-8") as f:
            data=json.load(f)
    except Exception as exc:
        print(f"polish_base_layout_rejected reason=read_error error={exc}", file=sys.stderr)
        return None
    placements=data.get("placements",[])
    if not isinstance(placements,list) or len(placements)!=N:
        print(f"polish_base_layout_rejected reason=count jsonCount={len(placements) if isinstance(placements,list) else -1} expected={N}", file=sys.stderr)
        return None
    name_to_index={name:i for i,(name,_) in enumerate(raw)}
    normalized_name_to_index={re.sub(r"^\d{3}_","",name):i for i,(name,_) in enumerate(raw)}
    entries=[]
    seen=set()
    for fallback_order,placement in enumerate(placements):
        if not isinstance(placement,dict):
            return None
        name=str(placement.get("name",""))
        i=name_to_index.get(name)
        if i is None:
            i=normalized_name_to_index.get(re.sub(r"^\d{3}_","",name))
        if i is None:
            print(f"polish_base_layout_rejected reason=name_missing name={name}", file=sys.stderr)
            return None
        if i in seen:
            print(f"polish_base_layout_rejected reason=duplicate name={name}", file=sys.stderr)
            return None
        seen.add(i)
        down=max(1,int(placement.get("mask_downsample",DOWN) or DOWN))
        if "mask_x" in placement and "mask_y" in placement:
            x=int(round(float(placement["mask_x"])/down))
            y=int(round(float(placement["mask_y"])/down))
        else:
            x=int(round(float(placement.get("x",0))/down))-G
            y=int(round(float(placement.get("y",0))/down))-G
        r=int(round(float(placement.get("angle",0))))%360
        s=clamp_scale(i,float(placement.get("scale",1.0)))
        order=int(placement.get("layer_order",fallback_order))
        entries.append((order,i,x,y,r,s))
    if len(seen)!=N:
        print(f"polish_base_layout_rejected reason=missing_names seen={len(seen)} expected={N}", file=sys.stderr)
        return None
    entries.sort(key=lambda entry:entry[0])
    polish_base_layout=[(i,x,y,r,s) for _,i,x,y,r,s in entries]
    occ=BASE_OCC.copy()
    for i,x,y,r,s in polish_base_layout:
        m=make(i,r,s,gap=True)
        h,w=m.shape
        if x<0 or y<0 or x+w>SW or y+h>SH:
            print(f"polish_base_layout_rejected reason=out_of_bounds name={raw[i][0]} x={x} y={y}", file=sys.stderr)
            return None
        region=occ[y:y+h,x:x+w]
        if region.shape!=m.shape or (region&m).any():
            print(f"polish_base_layout_rejected reason=collision_or_reserved name={raw[i][0]} x={x} y={y}", file=sys.stderr)
            return None
        stamp(occ,x,y,m)
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED=metadata_bool(data.get("right_center_void_chain_relocate_ever_applied",data.get("right_center_void_chain_relocate_applied",False)))
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_MOVES=metadata_int(data.get("right_center_void_chain_relocate_ever_moves",data.get("right_center_void_chain_relocate_moves",0)),0)
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_ALPHA_GAIN=metadata_float(data.get("right_center_void_chain_relocate_ever_alpha_gain",data.get("right_center_void_chain_relocate_alpha_gain",0.0)),0.0)
    RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_VOID_GAIN=metadata_float(data.get("right_center_void_chain_relocate_ever_void_gain",data.get("right_center_void_chain_relocate_void_gain",0.0)),0.0)
    refresh_right_center_void_chain_carryforward()
    if RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED:
        print(f"right_center_void_chain_carryforward_from_base applied=True moves={RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_MOVES} alpha_gain={RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_ALPHA_GAIN:.4f} void_gain={RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_VOID_GAIN:.4f}", file=sys.stderr)
    return polish_base_layout

if POLISH_BASE_JSON:
    polish_base_layout=load_polish_base_layout(POLISH_BASE_JSON)
    if polish_base_layout is not None:
        polish_base_alpha=material_alpha_topup_alpha(polish_base_layout)
        polish_candidate=material_alpha_topup(polish_base_layout, rounds=1)
        polish_candidate=multi_piece_material_topup(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_BAND_VOID_FILL:
            polish_candidate=band_void_fill_relocate(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR:
            polish_candidate=band_void_fill_pair_relocate(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE:
            polish_candidate=right_center_void_relocate(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE:
            polish_candidate=right_center_void_chain_relocate(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW:
            polish_candidate=structural_micro_grow(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_SCALE_TRANSFER:
            polish_candidate=scale_transfer_repack(polish_candidate, rounds=1)
        if LOW_ALPHA_READABLE_POSTPROCESS and LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK:
            polish_candidate=small_group_material_repack(polish_candidate, rounds=1)
        bestpl=polish_candidate
        best=layout_quality(bestpl)
        bestInk=ink(bestpl)
        polish_final_alpha=material_alpha_topup_alpha(bestpl)
        refresh_right_center_void_chain_carryforward()
        print(f"polish_base_layout_used path={POLISH_BASE_JSON} alpha={polish_base_alpha*100:.3f}->{polish_final_alpha*100:.3f}% materialTopup={MATERIAL_ALPHA_TOPUP_APPLIED} multiPieceTopup={MULTI_PIECE_TOPUP_APPLIED} structuralMicroGrow={STRUCTURAL_MICRO_GROW_APPLIED} structuralBlockerShrink={STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK} scaleTransfer={SCALE_TRANSFER_APPLIED} smallGroupRepack={SMALL_GROUP_MATERIAL_REPACK_APPLIED} bandVoidFill={BAND_VOID_FILL_APPLIED} bandVoidPair={BAND_VOID_FILL_PAIR_APPLIED} rightCenterVoid={RIGHT_CENTER_VOID_RELOCATE_APPLIED} rightCenterVoidChain={RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED} rightCenterVoidChainEver={RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED}", file=sys.stderr)

if bestpl is not None and not POLISH_BASE_JSON:
    for _cyc in range(3):
        candidate=compact(bestpl, rounds=2)
        candidate=growfill(candidate, rounds=4)
        candidate=manual_row_rebalance(candidate, rounds=1)
        candidate=micro_refit(candidate, rounds=2)
        if _cyc == 0:
            candidate=void_relocate(candidate, rounds=1)
        candidate_q=layout_quality(candidate)
        candidate_ink=ink(candidate)
        if candidate_q>=best-0.020 or candidate_ink>=bestInk+0.004:
            bestpl=candidate;best=max(best,candidate_q);bestInk=max(bestInk,candidate_ink)
    candidate=manual_row_rebalance(bestpl, rounds=2)
    candidate=micro_refit(candidate, rounds=3)
    candidate=local_cluster_repack(candidate, rounds=1)
    candidate=material_alpha_topup(candidate, rounds=1)
    candidate=multi_piece_material_topup(candidate, rounds=1)
    candidate=local_adapter_repack(candidate, rounds=1)
    if LOCAL_ADAPTER_V2:
        candidate=local_adapter_repack(candidate, rounds=1, v2_pass=True)
    candidate=structural_micro_grow(candidate, rounds=1)
    candidate=scale_transfer_repack(candidate, rounds=1)
    candidate=small_group_material_repack(candidate, rounds=1)
    candidate_q=layout_quality(candidate)
    candidate_ink=ink(candidate)
    candidate_exported_alpha=material_alpha_topup_alpha(candidate)
    best_exported_alpha=material_alpha_topup_alpha(bestpl)
    candidate_audit=visual_audit_like(candidate)
    best_audit=visual_audit_like(bestpl)
    if candidate_q>=best-0.010 or candidate_ink>=bestInk+0.003 or candidate_exported_alpha>=best_exported_alpha+0.0002 or candidate_audit["selection"]>=best_audit["selection"]+500:
        bestpl=candidate;best=candidate_q;bestInk=candidate_ink
    candidate=upside_rescue_refit(bestpl, rounds=4)
    if orientation_stats(candidate)["upside"]<orientation_stats(bestpl)["upside"]:
        candidate_q=layout_quality(candidate)
        candidate_ink=ink(candidate)
        if candidate_ink>=max(UPSIDE_RESCUE_MIN_ALPHA, bestInk-UPSIDE_RESCUE_MAX_ALPHA_LOSS) and candidate_q>=best-0.18:
            bestpl=candidate;best=candidate_q;bestInk=candidate_ink
# 输出 JSON(全分辨率像素中心 + 角度 + 缩放)
# 覆盖率指标
sheetW_px=int(SW*DOWN); sheetH_px=int(SH*DOWN)
refresh_right_center_void_chain_carryforward()
if bestpl is None:
    json.dump({
        "version":1,"paper_w_mm":PW,"paper_h_mm":PH,"dpi":int(DPI),"gap_mm":GAP,"target_long_side_mm":BASE_MM,
        "edge_safety_mm":EDGE_SAFETY_MM,
        "gap_model":GAP_MODEL,
        "mask_downsample":DOWN,
        "seed":SEED,
        "human_imitation":HUMAN_IMITATION,
        "manual_stagger":MANUAL_STAGGER,
        "manual_stagger_rotate":MANUAL_STAGGER_ROTATE,
        "manual_stagger_safe_rotate":MANUAL_STAGGER_SAFE_ROTATE,
        "row_phase_base_probe":ROW_PHASE_BASE_PROBE,
        "stagger_slot_beam_seed":STAGGER_SLOT_BEAM_SEED,
        "void_relocate":VOID_RELOCATE,
        "manual_row_rebalance":MANUAL_ROW_REBALANCE,
        "micro_refit":MICRO_REFIT,
        "local_cluster_repack":LOCAL_CLUSTER_REPACK,
        "material_alpha_topup":MATERIAL_ALPHA_TOPUP,
        "material_alpha_topup_applied":False,
        "material_alpha_topup_target":round(float(MATERIAL_ALPHA_TOPUP_TARGET),4),
        "material_alpha_topup_min_gain":round(float(MATERIAL_ALPHA_TOPUP_MIN_GAIN),4),
        "material_alpha_topup_min_accept":round(float(MATERIAL_ALPHA_TOPUP_MIN_ACCEPT),4),
        "material_alpha_topup_partial":False,
        "material_alpha_topup_moves":0,
        "multi_piece_topup":MULTI_PIECE_TOPUP,
        "multi_piece_topup_applied":False,
        "multi_piece_topup_target":round(float(MULTI_PIECE_TOPUP_TARGET),4),
        "multi_piece_topup_min_accept":round(float(MULTI_PIECE_TOPUP_MIN_ACCEPT),4),
        "multi_piece_topup_moves":0,
        "local_adapter":LOCAL_ADAPTER,
        "local_adapter_v2":LOCAL_ADAPTER_V2,
        "local_adapter_applied":False,
        "local_adapter_v2_applied":False,
        "local_adapter_chain_rescue_applied":False,
        "structural_micro_grow":STRUCTURAL_MICRO_GROW,
        "structural_micro_grow_applied":False,
        "structural_micro_grow_blocker_shrink":STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK,
        "structural_micro_grow_min_accept":round(float(STRUCTURAL_MICRO_GROW_MIN_ACCEPT),4),
        "structural_micro_grow_moves":0,
        "scale_transfer":SCALE_TRANSFER,
        "scale_transfer_applied":False,
        "scale_transfer_min_accept":round(float(SCALE_TRANSFER_MIN_ACCEPT),4),
        "scale_transfer_node_limit":int(SCALE_TRANSFER_NODE_LIMIT),
        "scale_transfer_moves":0,
        "small_group_material_repack":SMALL_GROUP_MATERIAL_REPACK,
        "small_group_material_repack_applied":False,
        "small_group_material_repack_min_accept":round(float(SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT),4),
        "small_group_material_repack_node_limit":int(SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT),
        "small_group_material_repack_moves":0,
        "band_void_fill":LOW_ALPHA_READABLE_BAND_VOID_FILL,
        "band_void_fill_applied":False,
        "band_void_fill_min_accept":round(float(BAND_VOID_FILL_MIN_ACCEPT),4),
        "band_void_fill_node_limit":int(BAND_VOID_FILL_NODE_LIMIT),
        "band_void_fill_moves":0,
        "band_void_fill_pair":LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR,
        "band_void_fill_pair_applied":False,
        "band_void_fill_pair_min_void_gain":round(float(BAND_VOID_FILL_PAIR_MIN_VOID_GAIN),4),
        "band_void_fill_pair_node_limit":int(BAND_VOID_FILL_PAIR_NODE_LIMIT),
        "band_void_fill_pair_moves":0,
        "right_center_void_relocate":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE,
        "right_center_void_relocate_applied":False,
        "right_center_void_relocate_min_void_gain":round(float(RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN),4),
        "right_center_void_relocate_node_limit":int(RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT),
        "right_center_void_relocate_moves":0,
        "right_center_void_relocate_gain":0.0,
        "right_center_void_right_blank_before":round(float(RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE),4),
        "right_center_void_right_blank_after":round(float(RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER),4),
        "right_center_void_mid_right_blank_before":round(float(RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE),4),
        "right_center_void_mid_right_blank_after":round(float(RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER),4),
        "right_center_void_chain_relocate":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE,
        "right_center_void_chain_relocate_applied":False,
        "right_center_void_chain_relocate_base_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED,
        "right_center_void_chain_relocate_ever_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED,
        "right_center_void_chain_relocate_min_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN),4),
        "right_center_void_chain_relocate_min_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN),4),
        "right_center_void_chain_relocate_node_limit":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT),
        "right_center_void_chain_relocate_moves":0,
        "right_center_void_chain_relocate_alpha_gain":0.0,
        "right_center_void_chain_relocate_void_gain":0.0,
        "right_center_void_chain_second_backfill":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL,
        "right_center_void_chain_second_backfill_applied":False,
        "right_center_void_chain_second_backfills":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS),
        "right_center_void_chain_second_backfill_moves":0,
        "right_center_void_chain_second_backfill_min_extra_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN),4),
        "right_center_void_chain_second_backfill_min_extra_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN),4),
        "right_center_void_chain_second_backfill_residual_target":RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET,
        "right_center_void_chain_second_backfill_extra_alpha_gain":0.0,
        "right_center_void_chain_second_backfill_extra_void_gain":0.0,
        "right_center_void_chain_relocate_ever_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES),
        "right_center_void_chain_relocate_ever_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN),4),
        "right_center_void_chain_relocate_ever_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN),4),
        "right_center_void_chain_right_blank_before":round(float(RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_BEFORE),4),
        "right_center_void_chain_right_blank_after":round(float(RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER),4),
        "right_center_void_chain_mid_right_blank_before":round(float(RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_BEFORE),4),
        "right_center_void_chain_mid_right_blank_after":round(float(RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER),4),
        "local_adapter_target_mode":LOCAL_ADAPTER_TARGET_MODE,
        "local_adapter_min_accept":round(float(LOCAL_ADAPTER_MIN_ACCEPT),4),
        "local_adapter_min_gain":round(float(LOCAL_ADAPTER_MIN_GAIN),4),
        "local_adapter_node_limit":int(LOCAL_ADAPTER_NODE_LIMIT),
        "local_adapter_max_cluster_size":int(LOCAL_ADAPTER_MAX_CLUSTER_SIZE),
        "local_adapter_v2_min_accept":round(float(LOCAL_ADAPTER_V2_MIN_ACCEPT),4),
        "local_adapter_moves":0,
        "manual_pose_score":0.0,
        "quality_score":0.0,
        "orientation_stats":{},
        "readability_guard_enabled":READABILITY_GUARD,
        "readability_score":0.0,
        "angle_histogram":{},
        "row_orientation_stats":[],
        "orientation_thresholds":orientation_thresholds(),
        "sheet_w_px":sheetW_px,"sheet_h_px":sheetH_px,
        "alpha":0.0,"coverage_bbox":0.0,
        "count":0,"placements":[]
    }, open(out_json,"w"), ensure_ascii=False, indent=2)
    print(f"no_layout placed=0/{N} targetLongSideMM={BASE_MM:.1f} seed={SEED} -> {out_json}")
    sys.exit(0)
occ_ink=np.zeros((SH,SW),bool); occ_bb=np.zeros((SH,SW),bool)
for i,x,y,r,s in bestpl:
    m=make(i,r,s,gap=False);hh,ww=m.shape
    y0=y+G;x0=x+G;y1=min(SH,y0+hh);x1=min(SW,x0+ww)
    if y1>y0 and x1>x0: occ_ink[y0:y1,x0:x1]|=m[:y1-y0,:x1-x0]
    mg=make(i,r,s);H2,W2=mg.shape;yb=min(SH,y+H2);xb=min(SW,x+W2)
    occ_bb[y:yb,x:xb]=True
alpha_cov=float(occ_ink.sum())/(SW*SH); bbox_cov=float(occ_bb.sum())/(SW*SH)
orient=orientation_stats(bestpl)
angle_hist=angle_histogram(bestpl)
row_orient=row_orientation_stats(bestpl)
layout=[]
for order_i,(i,x,y,r,s) in enumerate(bestpl):
    mc=make(i,r,s,gap=False);hh,ww=mc.shape   # 内容(不含间距)在工作格
    mg=make(i,r,s,gap=True)
    layout.append({
        "name":raw[i][0],
        "x":int((x+G)*DOWN),          # 内容左上角 x(全分辨率像素)
        "y":int((y+G)*DOWN),          # 内容左上角 y
        "w":int(ww*DOWN),             # 内容宽(px)
        "h":int(hh*DOWN),             # 内容高(px)
        "mask_x":int(x*DOWN),         # 含间距 mask 左上角 x(全分辨率像素)
        "mask_y":int(y*DOWN),         # 含间距 mask 左上角 y
        "mask_w":int(mg.shape[1]),    # 含间距的外部工作格 mask 宽
        "mask_h":int(mg.shape[0]),    # 含间距的外部工作格 mask 高
        "mask_downsample":DOWN,
        "mask_runs":mask_runs(mg),
        "angle":int(r),               # 旋转角(度, 逆时针)
        "orientation_bucket":orientation_bucket(r),
        "scale":round(float(s),4),    # 相对长边108mm基准的缩放
        "layer_order":order_i         # 0=最先放(底层), 越大越上层
    })
json.dump({
    "version":1,"paper_w_mm":PW,"paper_h_mm":PH,"dpi":int(DPI),"gap_mm":GAP,"target_long_side_mm":BASE_MM,
    "edge_safety_mm":EDGE_SAFETY_MM,
    "gap_mm_effective":round(EFFECTIVE_GAP_MM,2),
    "gap_model":GAP_MODEL,
    "mask_downsample":DOWN,
    "seed":SEED,
    "human_imitation":HUMAN_IMITATION,
    "manual_stagger":MANUAL_STAGGER,
    "manual_stagger_rotate":MANUAL_STAGGER_ROTATE,
    "manual_stagger_safe_rotate":MANUAL_STAGGER_SAFE_ROTATE,
    "row_phase_base_probe":ROW_PHASE_BASE_PROBE,
    "stagger_slot_beam_seed":STAGGER_SLOT_BEAM_SEED,
    "void_relocate":VOID_RELOCATE,
    "manual_row_rebalance":MANUAL_ROW_REBALANCE,
    "micro_refit":MICRO_REFIT,
    "local_cluster_repack":LOCAL_CLUSTER_REPACK,
    "material_alpha_topup":MATERIAL_ALPHA_TOPUP,
    "material_alpha_topup_applied":MATERIAL_ALPHA_TOPUP_APPLIED,
    "material_alpha_topup_target":round(float(MATERIAL_ALPHA_TOPUP_TARGET),4),
    "material_alpha_topup_min_gain":round(float(MATERIAL_ALPHA_TOPUP_MIN_GAIN),4),
    "material_alpha_topup_min_accept":round(float(MATERIAL_ALPHA_TOPUP_MIN_ACCEPT),4),
    "material_alpha_topup_partial":MATERIAL_ALPHA_TOPUP_PARTIAL,
    "material_alpha_topup_moves":int(MATERIAL_ALPHA_TOPUP_MOVES),
    "multi_piece_topup":MULTI_PIECE_TOPUP,
    "multi_piece_topup_applied":MULTI_PIECE_TOPUP_APPLIED,
    "multi_piece_topup_target":round(float(MULTI_PIECE_TOPUP_TARGET),4),
    "multi_piece_topup_min_accept":round(float(MULTI_PIECE_TOPUP_MIN_ACCEPT),4),
    "multi_piece_topup_moves":int(MULTI_PIECE_TOPUP_MOVES),
    "local_adapter":LOCAL_ADAPTER,
    "local_adapter_v2":LOCAL_ADAPTER_V2,
    "local_adapter_applied":LOCAL_ADAPTER_APPLIED,
    "local_adapter_v2_applied":LOCAL_ADAPTER_V2_APPLIED,
    "local_adapter_chain_rescue_applied":LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED,
    "structural_micro_grow":STRUCTURAL_MICRO_GROW,
    "structural_micro_grow_applied":STRUCTURAL_MICRO_GROW_APPLIED,
    "structural_micro_grow_blocker_shrink":STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK,
    "structural_micro_grow_min_accept":round(float(STRUCTURAL_MICRO_GROW_MIN_ACCEPT),4),
    "structural_micro_grow_moves":int(STRUCTURAL_MICRO_GROW_MOVES),
    "scale_transfer":SCALE_TRANSFER,
    "scale_transfer_applied":SCALE_TRANSFER_APPLIED,
    "scale_transfer_min_accept":round(float(SCALE_TRANSFER_MIN_ACCEPT),4),
    "scale_transfer_node_limit":int(SCALE_TRANSFER_NODE_LIMIT),
    "scale_transfer_moves":int(SCALE_TRANSFER_MOVES),
    "small_group_material_repack":SMALL_GROUP_MATERIAL_REPACK,
    "small_group_material_repack_applied":SMALL_GROUP_MATERIAL_REPACK_APPLIED,
    "small_group_material_repack_min_accept":round(float(SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT),4),
    "small_group_material_repack_node_limit":int(SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT),
    "small_group_material_repack_moves":int(SMALL_GROUP_MATERIAL_REPACK_MOVES),
    "band_void_fill":LOW_ALPHA_READABLE_BAND_VOID_FILL,
    "band_void_fill_applied":BAND_VOID_FILL_APPLIED,
    "band_void_fill_min_accept":round(float(BAND_VOID_FILL_MIN_ACCEPT),4),
    "band_void_fill_node_limit":int(BAND_VOID_FILL_NODE_LIMIT),
    "band_void_fill_moves":int(BAND_VOID_FILL_MOVES),
    "band_void_fill_pair":LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR,
    "band_void_fill_pair_applied":BAND_VOID_FILL_PAIR_APPLIED,
    "band_void_fill_pair_min_void_gain":round(float(BAND_VOID_FILL_PAIR_MIN_VOID_GAIN),4),
    "band_void_fill_pair_node_limit":int(BAND_VOID_FILL_PAIR_NODE_LIMIT),
    "band_void_fill_pair_moves":int(BAND_VOID_FILL_PAIR_MOVES),
    "right_center_void_relocate":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE,
    "right_center_void_relocate_applied":RIGHT_CENTER_VOID_RELOCATE_APPLIED,
    "right_center_void_relocate_min_void_gain":round(float(RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN),4),
    "right_center_void_relocate_node_limit":int(RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT),
    "right_center_void_relocate_moves":int(RIGHT_CENTER_VOID_RELOCATE_MOVES),
    "right_center_void_relocate_gain":round(float(RIGHT_CENTER_VOID_RELOCATE_GAIN),4),
    "right_center_void_right_blank_before":round(float(RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE),4),
    "right_center_void_right_blank_after":round(float(RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER),4),
    "right_center_void_mid_right_blank_before":round(float(RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE),4),
    "right_center_void_mid_right_blank_after":round(float(RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER),4),
    "right_center_void_chain_relocate":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE,
    "right_center_void_chain_relocate_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED,
    "right_center_void_chain_relocate_base_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED,
    "right_center_void_chain_relocate_ever_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED,
    "right_center_void_chain_relocate_min_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN),4),
    "right_center_void_chain_relocate_min_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN),4),
    "right_center_void_chain_relocate_node_limit":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT),
    "right_center_void_chain_relocate_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES),
    "right_center_void_chain_relocate_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN),4),
    "right_center_void_chain_relocate_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN),4),
    "right_center_void_chain_second_backfill":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL,
    "right_center_void_chain_second_backfill_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED,
    "right_center_void_chain_second_backfills":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS),
    "right_center_void_chain_second_backfill_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MOVES),
    "right_center_void_chain_second_backfill_min_extra_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN),4),
    "right_center_void_chain_second_backfill_min_extra_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN),4),
    "right_center_void_chain_second_backfill_residual_target":RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET,
    "right_center_void_chain_second_backfill_extra_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN),4),
    "right_center_void_chain_second_backfill_extra_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN),4),
    "right_center_void_chain_relocate_ever_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES),
    "right_center_void_chain_relocate_ever_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN),4),
    "right_center_void_chain_relocate_ever_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN),4),
    "right_center_void_chain_right_blank_before":round(float(RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_BEFORE),4),
    "right_center_void_chain_right_blank_after":round(float(RIGHT_CENTER_VOID_CHAIN_RIGHT_BLANK_AFTER),4),
    "right_center_void_chain_mid_right_blank_before":round(float(RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_BEFORE),4),
    "right_center_void_chain_mid_right_blank_after":round(float(RIGHT_CENTER_VOID_CHAIN_MID_RIGHT_BLANK_AFTER),4),
    "local_adapter_target_mode":LOCAL_ADAPTER_TARGET_MODE,
    "local_adapter_min_accept":round(float(LOCAL_ADAPTER_MIN_ACCEPT),4),
    "local_adapter_min_gain":round(float(LOCAL_ADAPTER_MIN_GAIN),4),
    "local_adapter_node_limit":int(LOCAL_ADAPTER_NODE_LIMIT),
    "local_adapter_max_cluster_size":int(LOCAL_ADAPTER_MAX_CLUSTER_SIZE),
    "local_adapter_v2_min_accept":round(float(LOCAL_ADAPTER_V2_MIN_ACCEPT),4),
    "local_adapter_moves":int(LOCAL_ADAPTER_MOVES),
    "manual_pose_score":round(float(manual_pose_score(bestpl)),4),
    "quality_score":round(float(layout_quality(bestpl)),4),
    "orientation_stats":{k:round(float(v),4) if isinstance(v,float) else int(v) for k,v in orient.items()},
    "readability_guard_enabled":READABILITY_GUARD,
    "readability_score":round(float(orientation_readability_score(bestpl)),4),
    "angle_histogram":angle_hist,
    "row_orientation_stats":row_orient,
    "orientation_thresholds":orientation_thresholds(),
    "sheet_w_px":sheetW_px,"sheet_h_px":sheetH_px,
    "alpha":round(alpha_cov,4),"coverage_bbox":round(bbox_cov,4),
    "count":len(bestpl),"placements":layout
}, open(out_json,"w"), ensure_ascii=False, indent=2)
print(f"ink(墨量)={alpha_cov*100:.1f}%  bbox={bbox_cov*100:.1f}%  placed={len(bestpl)}/{N} upright={orient['upright']} upside={orient['upside']} sideways={orient['sideways']} hard={orient['hard']} seed={SEED}  -> {out_json}")
# 预览
out=np.full((SH,SW,3),245,np.uint8);rng=np.random.default_rng(1)
for i,x,y,r,s in bestpl:
    m=make(i,r,s,gap=False);col=rng.integers(60,220,3);reg=out[y:y+m.shape[0],x:x+m.shape[1]];reg[m]=col
cv2.imwrite(out_json+".preview.png", out[:,:,::-1])

# ===== 真实贴纸合成预览(带白色kiss-cut刀边)=====
def render_real(bestpl, path, PUP=5):
    Hc,Wc=SH*PUP, SW*PUP
    canvas=np.full((Hc,Wc,3),245,np.uint8)
    for i,x,y,r,s in bestpl:
        # 原图 RGBA
        im=cv2.imread(files_full[i], cv2.IMREAD_UNCHANGED)
        if im is None: continue
        if im.ndim==3 and im.shape[2]==4:
            ys,xs=np.where(im[:,:,3]>30); im=im[ys.min():ys.max()+1, xs.min():xs.max()+1]
            bgr=im[:,:,:3]; al=im[:,:,3]
        else:
            bgr=im if im.ndim==3 else cv2.cvtColor(im,cv2.COLOR_GRAY2BGR); al=np.full(bgr.shape[:2],255,np.uint8)
        h,w=al.shape; f=BASE*s/max(h,w)*PUP
        nw,nh=max(1,int(w*f)),max(1,int(h*f))
        bgr=cv2.resize(bgr,(nw,nh)); al=cv2.resize(al,(nw,nh))
        if r%360:
            M=cv2.getRotationMatrix2D((nw/2,nh/2),r,1.0)
            cosA,sinA=abs(M[0,0]),abs(M[0,1]);NW=int(nh*sinA+nw*cosA);NH=int(nh*cosA+nw*sinA)
            M[0,2]+=NW/2-nw/2;M[1,2]+=NH/2-nh/2
            bgr=cv2.warpAffine(bgr,M,(NW,NH));al=cv2.warpAffine(al,M,(NW,NH))
        H2,W2=al.shape
        # 白色刀边:alpha 膨胀
        halo=cv2.dilate((al>30).astype(np.uint8),np.ones((max(3,PUP*2),max(3,PUP*2)),np.uint8))
        # 放到画布:中心对齐 cx,cy
        cx=int((x+make(i,r,s).shape[1]/2)*PUP); cy=int((y+make(i,r,s).shape[0]/2)*PUP)
        ox=cx-W2//2; oy=cy-H2//2
        for yy in range(H2):
            Y=oy+yy
            if Y<0 or Y>=Hc: continue
            row_al=al[yy]; row_halo=halo[yy]; row_bgr=bgr[yy]
            for xx in range(W2):
                X=ox+xx
                if X<0 or X>=Wc: continue
                if row_al[xx]>30: canvas[Y,X]=row_bgr[xx]
                elif row_halo[xx]: canvas[Y,X]=(255,255,255)
    cv2.imwrite(path, canvas)
files_full=[f for f in sorted(glob.glob(os.path.join(folder,"*.png"))) if cv2.imread(f,cv2.IMREAD_UNCHANGED) is not None]
render_real(bestpl, out_json+".real.png")
print("real preview ->", out_json+".real.png")
