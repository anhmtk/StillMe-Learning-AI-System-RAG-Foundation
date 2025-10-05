# BEGIN: NORMALIZE_HELPERS
from typing import Any, cast

from .types import ContainerSecurityContext, ContainerSpec, PodSpec, PodTemplateSpec


def extract_template_spec(obj: dict[str, Any]) -> PodTemplateSpec | None:
    # Guard 1: template
    if "template" not in obj or not isinstance(obj["template"], dict):
        return None
    template = cast(dict[str, Any], obj["template"])  # validated above - is dict

    # Guard 2: spec
    if "spec" not in template or not isinstance(template["spec"], dict):
        return None
    spec_dict = cast(dict[str, Any], template["spec"])  # validated above - is dict

    # Guard 3: containers
    if "containers" not in spec_dict or not isinstance(spec_dict["containers"], list):
        return None
    raw_containers = cast(list[Any], spec_dict["containers"])  # validated above - is list

    typed_containers: list[ContainerSpec] = []
    for c in raw_containers:
        if not isinstance(c, dict):
            continue
        # validated above - c is dict
        c_dict = cast(dict[str, Any], c)
        name_val = c_dict["name"] if "name" in c_dict else ""
        image_val = c_dict["image"] if "image" in c_dict else ""
        container: ContainerSpec = {
            "name": str(name_val),
            "image": str(image_val),
        }
        if "securityContext" in c_dict and isinstance(c_dict["securityContext"], dict):
            sc_dict = cast(dict[str, Any], c_dict["securityContext"])  # validated above - is dict
            sc: ContainerSecurityContext = {}
            # map có guard key-in → indexing, không dùng .get()
            if "runAsUser" in sc_dict and isinstance(sc_dict["runAsUser"], int):
                sc["runAsUser"] = sc_dict["runAsUser"]
            if "runAsGroup" in sc_dict and isinstance(sc_dict["runAsGroup"], int):
                sc["runAsGroup"] = sc_dict["runAsGroup"]
            if "runAsNonRoot" in sc_dict and isinstance(sc_dict["runAsNonRoot"], bool):
                sc["runAsNonRoot"] = sc_dict["runAsNonRoot"]
            if "allowPrivilegeEscalation" in sc_dict and isinstance(sc_dict["allowPrivilegeEscalation"], bool):
                sc["allowPrivilegeEscalation"] = sc_dict["allowPrivilegeEscalation"]
            if "readOnlyRootFilesystem" in sc_dict and isinstance(sc_dict["readOnlyRootFilesystem"], bool):
                sc["readOnlyRootFilesystem"] = sc_dict["readOnlyRootFilesystem"]
            if "capabilities" in sc_dict and isinstance(sc_dict["capabilities"], dict):
                # Optional: validate nội dung list[str]
                caps_dict = cast(dict[str, Any], sc_dict["capabilities"])  # validated above - is dict
                sc["capabilities"] = {str(k): v for k, v in caps_dict.items() if isinstance(v, list)}
            if len(sc):
                container["securityContext"] = sc
        typed_containers.append(container)

    tpl: PodTemplateSpec = {"spec": {"containers": typed_containers}}
    return tpl

def iter_containers(tpl: PodTemplateSpec | None) -> list[ContainerSpec]:
    if not tpl:
        return []
    # TypedDict guard + indexing
    if "spec" not in tpl:
        return []
    spec: PodSpec = tpl["spec"]
    if "containers" not in spec:
        return []
    return spec["containers"]
# END: NORMALIZE_HELPERS
