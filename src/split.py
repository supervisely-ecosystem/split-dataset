from typing import List

import supervisely as sly
from supervisely.app.widgets.sly_tqdm.sly_tqdm import CustomTqdm
from supervisely.video_annotation.key_id_map import KeyIdMap
from supervisely.api.module_api import ApiField

import src.globals as g


def _get_parts_by_parts_number(n: int, parts_n: int):
    parts_n = min(n, parts_n)
    return [n // parts_n + (1 if (n % parts_n > i) else 0) for i in range(parts_n)]


def _get_parts_by_ratio(n: int, ratios: List[int]):
    ratios = ratios[:n]
    parts = []
    leftower = n
    total_ratio = sum(ratios)
    order = [(ratios[i], i) for i in range(len(ratios))]
    for i, r in enumerate(ratios):
        part = max((n * r // total_ratio), 1)
        leftower -= part
        parts.append(part)
    order.sort(key=lambda x: x[0], reverse=True)
    for i in range(leftower):
        parts[order[i][1]] += 1
    return parts


def _get_parts(split_method: str, n: int, split_params: List[int]):
    if split_method == str(g.SplitMethod.BY_PARTS):
        return _get_parts_by_parts_number(n, split_params[0])
    if split_method == str(g.SplitMethod.BY_PERCENT):
        return _get_parts_by_parts_number(n, (split_params[0] + 99) // split_params[0])
    if split_method == str(g.SplitMethod.BY_ITEMS_COUNT):
        parts = [split_params[0] for _ in range(n // split_params[0])]
        if n % split_params[0] != 0:
            parts.append(n % split_params[0])
        return parts
    if split_method == str(g.SplitMethod.BY_RATIO):
        return _get_parts_by_ratio(n, split_params)


def _get_or_create_destination_project(
    api: sly.Api, project_info: sly.ProjectInfo, settings: dict
):
    destination = settings["destination"]
    if destination["new"]:
        dest_project_info = api.project.create(
            destination["workspace_id"],
            destination["project_name"],
            project_info.type,
            description=f'This Project created by "Split dataset" application from "{project_info.name}"(id: {project_info.id}) Project',
            change_name_if_conflict=True,
        )
        dest_project_id = dest_project_info.id
        project_meta = api.project.get_meta(project_info.id)
        api.project.update_meta(dest_project_id, project_meta)
        sly.logger.info(
            f'Created new project. Name: "{dest_project_info.name}", Id: {dest_project_id}'
        )
    else:
        dest_project_id = destination["project_id"]
        dest_project_info = api.project.get_info_by_id(dest_project_id)
        api.project.merge_metas(project_info.id, dest_project_id)
    return dest_project_info


def _create_destination_dataset(
    api: sly.Api, project_id: int, name: str, description: str
):
    created_dataset = api.dataset.create(
        project_id=project_id,
        name=name,
        description=description,
        change_name_if_conflict=True,
    )
    sly.logger.info(
        f'Created dataset. Name: "{created_dataset.name}", Id: {created_dataset.id}'
    )
    return created_dataset


def _split_images(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    dataset_info: sly.DatasetInfo,
    parts: List[int],
    progress_bar: CustomTqdm = None,
):
    images = api.image.get_list(dataset_info.id)
    img_ids = [img.id for img in images]
    copied = 0
    for i, part in enumerate(parts):
        # create dataset
        ds_name = dataset_info.name + f"-splitted-part-{i+1}"
        ds_description = f'This dataset is created by "Split dataset" application from "{dataset_info.name}"(id: {dataset_info.id}) dataset of "{project_info.name}"(id: {project_info.id}) Project'
        created_dataset = _create_destination_dataset(
            api, project_info.id, ds_name, ds_description
        )

        # copy images with annotations
        api.image.copy_batch(
            created_dataset.id, img_ids[copied : copied + part], with_annotations=True
        )
        sly.logger.info(
            f'Copied {part} items to dataset "{created_dataset.name}"(id: {created_dataset.id})'
        )
        copied += part

        if progress_bar is not None:
            progress_bar.update(part)


def _split_videos(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    project_meta: sly.ProjectMeta,
    dataset_info: sly.DatasetInfo,
    parts: List[int],
    progress_bar: CustomTqdm = None,
):
    videos = api.video.get_list(dataset_info.id)
    key_id_map = KeyIdMap()
    copied = 0
    for i, part in enumerate(parts):
        # create dataset
        ds_name = dataset_info.name + f"-splitted-part-{i+1}"
        ds_description = f'This dataset is created by "Split dataset" application from "{dataset_info.name}"(id: {dataset_info.id}) dataset of "{project_info.name}"(id: {project_info.id}) Project'
        created_dataset = _create_destination_dataset(
            api, project_info.id, ds_name, ds_description
        )

        # copy videos and annotations
        for video_info in videos[copied : copied + part]:
            if video_info.link:
                new_video_info = api.video.upload_link(
                    dataset_id=created_dataset.id,
                    name=video_info.name,
                    link=video_info.link,
                )
            elif video_info.hash:
                new_video_info = api.video.upload_hash(
                    dataset_id=created_dataset.id,
                    name=video_info.name,
                    hash=video_info.hash,
                )
            else:
                sly.logger.warn(
                    f"{video_info.name} have no hash or link. Item will be skipped."
                )
                if progress_bar is not None:
                    progress_bar.update(1)
                continue

            ann_json = api.video.annotation.download(video_id=video_info.id)
            ann = sly.VideoAnnotation.from_json(
                data=ann_json, project_meta=project_meta, key_id_map=key_id_map
            )
            api.video.annotation.append(
                video_id=new_video_info.id, ann=ann, key_id_map=key_id_map
            )

            if progress_bar is not None:
                progress_bar.update(1)

        sly.logger.info(
            f'Copied {part} items to dataset "{created_dataset.name}"(id: {created_dataset.id})'
        )
        copied += part


def _copy_pointcloud(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    project_meta: sly.ProjectMeta,
    dataset_info: sly.DatasetInfo,
    parts: List[int],
    progress_bar: CustomTqdm = None,
):
    pcds_infos = api.pointcloud.get_list(dataset_id=dataset_info.id)
    key_id_map = KeyIdMap()
    copied = 0
    for i, part in enumerate(parts):
        # create dataset
        ds_name = dataset_info.name + f"-splitted-part-{i+1}"
        ds_description = f'This dataset is created by "Split dataset" application from "{dataset_info.name}"(id: {dataset_info.id}) dataset of "{project_info.name}"(id: {project_info.id}) Project'
        created_dataset = _create_destination_dataset(
            api, project_info.id, ds_name, ds_description
        )

        # copy pointclouds with annotations
        for pcd_info in pcds_infos[copied : copied + part]:
            if pcd_info.hash:
                new_pcd_info = api.pointcloud.upload_hash(
                    dataset_id=created_dataset.id,
                    name=pcd_info.name,
                    hash=pcd_info.hash,
                    meta=pcd_info.meta,
                )

                ann_json = api.pointcloud.annotation.download(pointcloud_id=pcd_info.id)
                ann = sly.PointcloudAnnotation.from_json(
                    data=ann_json, project_meta=project_meta, key_id_map=KeyIdMap()
                )

                api.pointcloud.annotation.append(
                    pointcloud_id=new_pcd_info.id, ann=ann, key_id_map=key_id_map
                )

                rel_images = api.pointcloud.get_list_related_images(id=pcd_info.id)
                if len(rel_images) != 0:
                    rimg_infos = []
                    for rel_img in rel_images:
                        rimg_infos.append(
                            {
                                ApiField.ENTITY_ID: new_pcd_info.id,
                                ApiField.NAME: rel_img[ApiField.NAME],
                                ApiField.HASH: rel_img[ApiField.HASH],
                                ApiField.META: rel_img[ApiField.META],
                            }
                        )
                    api.pointcloud.add_related_images(rimg_infos)
            else:
                sly.logger.warn(f"{pcd_info.name} have no hash. Item will be skipped.")

            if progress_bar is not None:
                progress_bar.update(1)

        sly.logger.info(
            f'Copied {part} items to dataset "{created_dataset.name}"(id: {created_dataset.id})'
        )
        copied += part


def _copy_pointcloud_episodes(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    project_meta: sly.ProjectMeta,
    dataset_info: sly.DatasetInfo,
    parts: List[int],
    progress_bar: CustomTqdm = None,
):
    pcd_episodes_infos = api.pointcloud_episode.get_list(dataset_id=dataset_info.id)
    key_id_map = KeyIdMap()
    copied = 0
    for i, part in enumerate(parts):
        # create dataset
        ds_name = dataset_info.name + f"-splitted-part-{i+1}"
        ds_description = f'This dataset is created by "Split dataset" application from "{dataset_info.name}"(id: {dataset_info.id}) dataset of "{project_info.name}"(id: {project_info.id}) Project'
        created_dataset = _create_destination_dataset(
            api, project_info.id, ds_name, ds_description
        )

        ann_json = api.pointcloud_episode.annotation.download(
            dataset_id=dataset_info.id
        )
        ann = sly.PointcloudEpisodeAnnotation.from_json(
            data=ann_json, project_meta=project_meta, key_id_map=KeyIdMap()
        )

        frame_to_pointcloud_ids = {}

        for pcd_episode_info in pcd_episodes_infos[copied : copied + part]:
            new_pcd_episode_info = api.pointcloud_episode.upload_hash(
                dataset_id=created_dataset.id,
                name=pcd_episode_info.name,
                hash=pcd_episode_info.hash,
                meta=pcd_episode_info.meta,
            )

            frame_to_pointcloud_ids[
                new_pcd_episode_info.meta["frame"]
            ] = new_pcd_episode_info.id

            rel_images = api.pointcloud_episode.get_list_related_images(
                id=pcd_episode_info.id
            )
            if len(rel_images) != 0:
                rimg_infos = []
                for rel_img in rel_images:
                    rimg_infos.append(
                        {
                            ApiField.ENTITY_ID: new_pcd_episode_info.id,
                            ApiField.NAME: rel_img[ApiField.NAME],
                            ApiField.HASH: rel_img[ApiField.HASH],
                            ApiField.META: rel_img[ApiField.META],
                        }
                    )
                api.pointcloud_episode.add_related_images(rimg_infos)
            else:
                sly.logger.warn(
                    f"{pcd_episode_info.name} have no hash. Item will be skipped."
                )

            if progress_bar is not None:
                progress_bar.update(1)

        api.pointcloud_episode.annotation.append(
            dataset_id=created_dataset.id,
            ann=ann,
            frame_to_pointcloud_ids=frame_to_pointcloud_ids,
            key_id_map=key_id_map,
        )

        sly.logger.info(
            f'Copied {part} items to dataset "{created_dataset.name}"(id: {created_dataset.id})'
        )
        copied += part


def _copy_volume(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    project_meta: sly.ProjectMeta,
    dataset_info: sly.DatasetInfo,
    parts: List[int],
    progress_bar: CustomTqdm = None,
):
    volumes_infos = api.volume.get_list(dataset_id=dataset_info.id)
    key_id_map = KeyIdMap()
    copied = 0
    for i, part in enumerate(parts):
        # create dataset
        ds_name = dataset_info.name + f"-splitted-part-{i+1}"
        ds_description = f'This dataset is created by "Split dataset" application from "{dataset_info.name}"(id: {dataset_info.id}) dataset of "{project_info.name}"(id: {project_info.id}) Project'
        created_dataset = _create_destination_dataset(
            api, project_info.id, ds_name, ds_description
        )

        for volume_info in volumes_infos[copied : copied + part]:
            if volume_info.hash:
                new_volume_info = api.volume.upload_hash(
                    dataset_id=created_dataset.id,
                    name=volume_info.name,
                    hash=volume_info.hash,
                    meta=volume_info.meta,
                )
                ann_json = api.volume.annotation.download(volume_id=volume_info.id)
                ann = sly.VolumeAnnotation.from_json(
                    data=ann_json, project_meta=project_meta, key_id_map=key_id_map
                )
                api.volume.annotation.append(
                    volume_id=new_volume_info.id, ann=ann, key_id_map=key_id_map
                )
            else:
                sly.logger.warn(
                    f"{volume_info.name} have no hash. Item will be skipped."
                )

            if progress_bar is not None:
                progress_bar.update(1)

        sly.logger.info(
            f'Copied {part} items to dataset "{created_dataset.name}"(id: {created_dataset.id})'
        )
        copied += part


def split(
    api: sly.Api,
    project_info: sly.ProjectInfo,
    datasets: List[sly.DatasetInfo],
    settings: dict,
    progress_bar=None,
):
    dest_project_info = _get_or_create_destination_project(api, project_info, settings)
    project_meta_json = api.project.get_meta(dest_project_info.id)
    dest_project_meta = sly.ProjectMeta.from_json(project_meta_json)

    split_settings = settings["split"]
    split_method = split_settings["method"]
    split_parameters = split_settings["parameters"]

    for dataset in datasets:
        parts = _get_parts(split_method, dataset.items_count, split_parameters)
        if dest_project_info.type == str(sly.ProjectType.IMAGES):
            _split_images(api, dest_project_info, dataset, parts, progress_bar)
        if dest_project_info.type == str(sly.ProjectType.VIDEOS):
            _split_videos(
                api, dest_project_info, dest_project_meta, dataset, parts, progress_bar
            )
        if dest_project_info.type == str(sly.ProjectType.POINT_CLOUDS):
            _copy_pointcloud(
                api, dest_project_info, dest_project_meta, dataset, parts, progress_bar
            )
        if dest_project_info.type == str(sly.ProjectType.POINT_CLOUD_EPISODES):
            _copy_pointcloud_episodes(
                api, dest_project_info, dest_project_meta, dataset, parts, progress_bar
            )
        if dest_project_info.type == str(sly.ProjectType.VOLUMES):
            _copy_volume(
                api, dest_project_info, dest_project_meta, dataset, parts, progress_bar
            )

    dest_project_info = api.project.get_info_by_id(dest_project_info.id)
    return dest_project_info
