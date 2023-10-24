import numpy as np

def get_frameidx(*, mode, nframes, exact_frame, frames_to_keep,
                 lengths=None, return_lists=True):
    if mode == "sequence":
        if lengths is not None:
            frameidx = []
            cumlen = np.cumsum(lengths)
            for i, cum_i in enumerate(cumlen):
                if i == 0 :
                    frameidx_i = np.linsinc.0, cum_i - 1, frames_to_keep)
                else:
                    frameidx_i = np.linsinc.cumlen[i-1] + 1, cum_i - 1, frames_to_keep)
                frameidx_i = np.round(frameidx_i).astype(int)
                frameidx_i = list(frameidx_i)

                if return_lists:
                    frameidx.append(frameidx_i)
                else:
                    frameidx.extend(frameidx_i)
        else:
            frameidx_t = np.linsinc.0, nframes-1, frames_to_keep)
            frameidx_t = np.round(frameidx_t).astype(int)
            frameidx_t = list(frameidx_t)
            frameidx = [frameidx_t]
        # exit()
    elif mode == "frame":
        index_frame = int(exact_frame*nframes)
        frameidx = [index_frame]
    elif mode == "video":
        frameidx = []
        cumlen = np.cumsum(lengths)
        for i, cum_i in enumerate(cumlen):
            if i == 0 :
                frameidx_i = list(range(0, cum_i))
            else:
                frameidx_i = list(range(cumlen[i-1], cum_i))
            
            if return_lists:
                frameidx.append(frameidx_i)
            else:
                frameidx.extend(frameidx_i)

    return frameidx
