def regroup_metrics(metrics):
    from sinc.info.joints import smplh_joints
    pose_names = smplh_joints[1:23]
    dico = {key: val.numpy() for key, val in metrics.items()}

    if "APE_pose" in dico:
        APE_pose = dico.pop("APE_pose")
        for name, ape in zip(pose_names, APE_pose):
            dico[f"APE_pose_{name}"] = ape

    if "APE_joints" in dico:
        APE_joints = dico.pop("APE_joints")
        for name, ape in zip(smplh_joints, APE_joints):
            dico[f"APE_joints_{name}"] = ape

    if "AVE_pose" in dico:
        AVE_pose = dico.pop("AVE_pose")
        for name, ave in zip(pose_names, AVE_pose):
            dico[f"AVE_pose_{name}"] = ave

    if "AVE_joints" in dico:
        AVE_joints = dico.pop("AVE_joints")
        for name, ape in zip(smplh_joints, AVE_joints):
            dico[f"AVE_joints_{name}"] = ave

    return dico


def sanitize(dico):
    dico = {key: "{:.5f}".format(float(val)) for key, val in dico.items()}
    return dico
