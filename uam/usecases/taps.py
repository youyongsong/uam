from uam.settings import BUILTIN_TAPS


def list_taps(TapsGateway):
    builtin_taps = BUILTIN_TAPS
    external_taps = TapsGateway.list_taps()
    return sorted(builtin_taps+external_taps,
                  key=lambda k: k['priority'], reverse=True)
