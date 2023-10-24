import bpy
import os
import sys
import numpy as np
import math

from .materials import colored_material
from .scene import setup_scene  # noqa
from .floor import show_traj, plot_floor, get_trajectory
from .vertices import prepare_vertices
from .tools import load_numpy_vertices_into_blender, delete_objs, mesh_detect
from .camera import Camera
from .sampler import get_frameidx
from .meshes import Meshes, prepare_meshes


def prune_begin_end(data, perc):
    to_remove = int(len(data)*perc)
    if to_remove == 0:
        return data
    return data[to_remove:-to_remove]


def render_current_frame(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(use_viewport=True, write_still=True)


def locate_action(idx, lens):
    cumsum = np.cumsum(lens)
    min_v = min(i for i in cumsum if i >= (idx+1))
    min_idx = list(cumsum).index(min_v)
    ind_norm = (idx - cumsum[min_idx-1]) if (idx - cumsum[min_idx-1]) >= 0 else idx
    return min_idx, ind_norm

def render(npydata, frames_folder, *, mode, faces_path,
           gt=False,
           exact_frame=None,
           num=2,
           color=None,
           downsample=True,
           canonicalize=True,
           always_on_floor=False,
           fake_translation=False,
           cycle=True, res='low',
           init=True,
           lengths=None,
           separate_actions=True,
           bp=False,
           texture_path=None):
    if init:
        # Setup the scene (lights / render engine / resolution etc)
        setup_scene(cycle=cycle, res=res)
    color_dict = {'blue':0,
                  'grey':1,
                  'purple':2,
                  'green':3,
                  'red':4}
    
    is_mesh = mesh_detect(npydata)
    if lengths is not None and isinstance(lengths, list):
        num_of_actions = len(lengths)
    else:
        num_of_actions = 1
    # Put everything in this folder
    if mode == "video":

        fake_translation = False
        separate_actions = False
        if always_on_floor:
            frames_folder += "_onfloor"
        os.makedirs(frames_folder, exist_ok=True)

        # if it is a mesh, it is already downsampled
        # if downsample: #and not is_mesh:
        #     npydata = npydata[::20]
    elif mode == "sequence":
        img_name, ext = os.path.splitext(frames_folder)
        if always_on_floor:
            img_name += "_onfloor"
        img_path = f"{img_name}{ext}"
    elif mode == "frame":
        img_name, ext = os.path.splitext(frames_folder)
        if always_on_floor:
            img_name += "_onfloor"
        img_path = f"{img_name}_{exact_frame}{ext}"
    fake = 'fake' if fake_translation else ''
    nframes = len(npydata)
    actions_bodies = []

    frameidxs = get_frameidx(mode=mode, nframes=nframes,
                             exact_frame=exact_frame,
                             frames_to_keep=num, lengths=lengths,
                             return_lists=True)

    if color is None:
        action_id = 0
    else:
        action_id = color_dict[color]

    data = prepare_meshes(npydata, 
                          canonicalize=canonicalize,
                          always_on_floor=always_on_floor)    
    for frameidx in frameidxs:
        action_bodies = npydata[frameidx]
        actions_bodies.append(action_bodies)

    all_actions_bodies = np.concatenate(actions_bodies)

    if mode == "sequence":
        total_num_of_rendered_frames = num * num_of_actions
    else:
        total_num_of_rendered_frames = len(all_actions_bodies)

    if mode == "sequence":
        if fake_translation:
            # center all of them
            # except in the gravity axis
            npydata[..., :2] -= npydata.mean(1)[:, None][..., :2]
            actions_bodies_transf = []
            factor = 1.5
            if not separate_actions:
                factor=3.0 # 3.0 for 2 action sin data
                shift_vals = factor * np.linsinc.-total_num_of_rendered_frames/2, total_num_of_rendered_frames/2, total_num_of_rendered_frames)/total_num_of_rendered_frames
                # shift_vals = factor * np.linsinc.0, total_num_of_rendered_frames, total_num_of_rendered_frames)/total_num_of_rendered_frames

                # shift_vals[(total_num_of_rendered_frames//2):] *= 1.3
                # shift_vals[:(total_num_of_rendered_frames//2)] *= 0.8
                for action_bodies, shift in zip(actions_bodies, [shift_vals[num*idx:num*(idx+1)] for idx in range(num_of_actions)]):
                    # put the fake translation
                    # and still 0 for gravity axis
                    action_bodies += np.stack((shift[:, None], shift[:, None], 0 * shift[:, None]), axis=2)
                    actions_bodies_transf.append(action_bodies)
            else:
                for action_bodies in zip(actions_bodies):
                    shift = factor * np.linsinc.-num/2, num/2, num)/num
                    # put the fake translation
                    # and still 0 for gravity axis
                    action_bodies += np.stack((-shift[:, None], -shift[:, None], 0 * shift[:, None]), axis=2)
                    actions_bodies_transf.append(action_bodies)
        else:
            actions_bodies_transf = all_actions_bodies.reshape(num_of_actions, num, *all_actions_bodies.shape[1:])
    elif mode == 'video':
        actions_bodies_transf = actions_bodies
    all_actions_bodies = np.concatenate(actions_bodies_transf)

    # begin = 0
    # cameras_middle = []
    # cameras_middle.append(npydata[ids].mean(axis=(0, 1)))
    only_trans = np.mean(all_actions_bodies.reshape(-1, *all_actions_bodies.shape[2:]),
                                 axis=(0, 1))
    # only_trans = 0*np.mean([0.0, 0.0, 0.0], 0)

    if not separate_actions and mode == 'sequence':
        if is_mesh:
            from .meshes import Meshes

            data = Meshes(actions_bodies_transf, gt=gt, mode=mode,
                          faces_path=faces_path,
                          canonicalize=canonicalize,
                          always_on_floor=always_on_floor,
                          lengths=lengths,
                          action_id=action_id)

        # else:
        #     # TODO maybe need an update
        #     pass
        only_trans = all_actions_bodies.mean((0, 1))
        plot_floor(all_actions_bodies, color_alpha=None, texture_path=texture_path)
        camera = Camera(first_root=only_trans, mode=mode, is_mesh=is_mesh, fakeinone=True)
    elif mode == 'video':
        only_trans = all_actions_bodies.mean((0, 1))
        plot_floor(all_actions_bodies, color_alpha=None, texture_path=texture_path)
        camera = Camera(first_root=only_trans, mode=mode, is_mesh=is_mesh)
    img_paths = []
    imported_obj_names = []
    lengths_cum = np.cumsum(lengths)
    for action_id, action_bodies in enumerate(actions_bodies_transf):
        action_bodies = np.squeeze(action_bodies)
        if is_mesh:
            from .meshes import Meshes
            data = Meshes(action_bodies, gt=gt, mode=mode,
                          faces_path=faces_path,
                          canonicalize=canonicalize,
                          always_on_floor=always_on_floor,
                          lengths=lengths,
                          bp=bp,
                          action_id=action_id)
        else:
            # TODO maybe need an update
            from .joints import Joints
            data = Joints(action_bodies, gt=gt, mode=mode,
                          canonicalize=canonicalize,
                          always_on_floor=always_on_floor)

        if separate_actions and mode =='sequence':
            plot_floor(data.data, color_alpha=None)
            camera = Camera(first_root=action_bodies.mean((0, 1)), mode=mode, is_mesh=is_mesh)
            imported_obj_names = []
        # TODO camera
        # camera.update(data.get_mean_root())
        # camera.update(npydata[npydata.shape[0]//2].mean(0)+camera._root)

        # render the frames within an action
        number_of_single_action_loops = num if mode == 'sequence' else lengths[action_id]
        for idx in range(number_of_single_action_loops):
            islast_within_action = idx == num-1

            mat = data.get_sequence_mat(idx/(num-1))
            objname = data.load_in_blender(idx, mat)

            # name = f"{str(idx).zfill(4)}_{action_id}"

            if mode == "video":
                if action_id == 0:
                    name = f"{str(idx).zfill(4)}"
                else:
                    name = f"{str(idx+lengths_cum[action_id-1]).zfill(4)}"
                path = os.path.join(frames_folder, f"frame_{name}.png")
            else:
                # name = f"{str(idx).zfill(4)}_{action_id}"
                path = img_path

            if mode == "sequence":
                imported_obj_names.append(objname)
            elif mode == "frame":
                camera.update(data.get_root(frameidx))

            if mode == 'video' or mode == 'frame':
                render_current_frame(path)
                delete_objs(objname)
            elif mode == 'sequence':
                # camera.eye_view()
                if separate_actions and islast_within_action:
                    path = path.replace('.png', '')
                    img_paths.append(f'{path}_{action_id}{fake}.png')
                    render_current_frame(f'{path}_{action_id}{fake}.png')
                    # keeping blender file for loading later
                    fn = frames_folder.split('/')[-1]
                    fdn = '/'.join(frames_folder.split('/')[:-1])
                    bpy.ops.wm.save_as_mainfile(filepath=f"{fdn}/{fn.replace('.png', '')}.blend")

                    delete_objs(imported_obj_names)
                    delete_objs(["Plane", "myCurve", "Cylinder"])

    # render in the end only
    if not separate_actions and mode == 'sequence':
        path = path.replace('.png', '')
        img_paths.append(f'{path}_all{fake}.png')
        render_current_frame(f'{path}_all{fake}.png')
    # fn = frames_folder.split('/')[-1]
    # fdn = '/'.join(frames_folder.split('/')[:-1])
    # bpy.ops.wm.save_as_mainfile(filepath=f"{fdn}/{fn.replace('.png', '')}.blend")

    delete_objs(imported_obj_names)
    delete_objs(["Plane", "myCurve", "Cylinder"])

    if mode == "video":
        return frames_folder
    else:
        return img_paths
