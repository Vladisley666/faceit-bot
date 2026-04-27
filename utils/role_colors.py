def get_role_color(role_type, value):
    if role_type == "kd":
        if value < 0.9: return 0xffffff
        elif value < 1.0: return 0xd4f1f9
        elif value < 1.1: return 0xa4d8f0
        elif value < 1.2: return 0x74b9e7
        elif value < 1.3: return 0x4a9fd8
        elif value < 1.4: return 0x2e86c1
        elif value < 1.5: return 0x1f618d
        elif value < 1.6: return 0x117a65
        elif value < 1.7: return 0x1e8449
        elif value < 1.8: return 0xb7950b
        elif value < 1.9: return 0xb03a2e
        elif value < 2.0: return 0x943126
        else: return 0x000000
    elif role_type == "avg":
        if value < 10: return 0xffffff
        elif value < 11: return 0xd4f1f9
        elif value < 12: return 0xa4d8f0
        elif value < 13: return 0x74b9e7
        elif value < 14: return 0x4a9fd8
        elif value < 15: return 0x2e86c1
        elif value < 16: return 0x1f618d
        elif value < 17: return 0x117a65
        elif value < 18: return 0x1e8449
        elif value < 19: return 0xb7950b
        elif value < 20: return 0xb03a2e
        else: return 0xe67e22
    elif role_type == "map":
        return 0x9b59b6
    elif role_type == "level":
        level_colors = {1:0x992d22,2:0xa83227,3:0xb7382c,4:0xc63d31,5:0xd54236,6:0xe3473b,7:0xe74c3c,8:0xe95f4f,9:0xeb7263,10:0xed8576}
        return level_colors.get(value, 0xe74c3c)
    return 0x99aab5