import config.settings as cfg
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
import json

c = EnjaziClient()
get_valid_token(c)

with c:
    auth_header = {"Authorization": "Bearer " + c._token}
    inst_headers = {
        "x-behalf-id": "316",
        "x-behalf-on": "institution",
        "x-institution-id": str(cfg.CORPORATION_ID),
        "x-current-role": "3",
    }
    resp = c._session.get(
        cfg.BASE_URL + "/institution_panel/episodes",
        params={"page": 1, "limit": 3, "status": "true"},
        headers={**cfg.BASE_HEADERS, **inst_headers, **auth_header},
    )
    data = resp.json()

print("data keys:", list(data.get("data", {}).keys()) if isinstance(data.get("data"), dict) else type(data.get("data")))
d = data.get("data", {})
if isinstance(d, dict):
    for k, v in d.items():
        if isinstance(v, list) and v:
            print(f"\ndata.{k}[0]:")
            print(json.dumps(v[0], ensure_ascii=False, indent=2))
            break
elif isinstance(d, list) and d:
    print(json.dumps(d[0], ensure_ascii=False, indent=2))
