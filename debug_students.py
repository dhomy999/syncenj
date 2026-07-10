import sys
import config.settings as cfg
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
import json

c = EnjaziClient()
get_valid_token(c)

mode = sys.argv[1] if len(sys.argv) > 1 else "list"

with c:
    auth_header = {"Authorization": "Bearer " + c._token}

    # institution ID can be passed as last arg
    behalf_id = sys.argv[-1] if len(sys.argv) > 2 else cfg.INSTITUTION_ID

    inst_headers = {
        "x-behalf-id": str(behalf_id),
        "x-behalf-on": "institution",
        "x-institution-id": str(cfg.CORPORATION_ID),
        "x-current-role": "3",
    }

    if mode == "profile":
        student_id = sys.argv[2]
        resp = c._session.get(
            cfg.BASE_URL + f"/institution_panel/students/{student_id}/profile",
            headers={**cfg.BASE_HEADERS, **inst_headers, **auth_header},
        )
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

    elif mode == "list":
        resp = c._session.get(
            cfg.BASE_URL + "/institution_panel/students",
            params={"page": 1, "limit": 5},
            headers={**cfg.BASE_HEADERS, **inst_headers, **auth_header},
        )
        data = resp.json()
        print("Top keys:", list(data.keys()))
        if "data" in data:
            d = data["data"]
            print("data keys:", list(d.keys()) if isinstance(d, dict) else type(d))
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, list) and v:
                        print(f"\ndata.{k}[0]:")
                        print(json.dumps(v[0], ensure_ascii=False, indent=2))
                        break
            elif isinstance(d, list) and d:
                print("\ndata[0]:")
                print(json.dumps(d[0], ensure_ascii=False, indent=2))
