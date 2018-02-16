#!/usr/bin/env bash
#
# Use Hydra command line client to create a test client application with id
# "testclient" capable of requesting the scope required to access the lookup
# API.
#
set -xe
docker-compose exec hydra hydra clients create \
    --id testclient --secret secret \
    --grant-types implicit,authorization_code \
    --response-types token,code,refresh_token \
    --callbacks http://localhost:4445/callback,http://localhost:8000/static/iarbackend/oauth2-redirect.html,http://localhost:8080/static/lookupproxy/oauth2-redirect.html,http://localhost:3000/oauth2-callback \
    --allowed-scopes lookup:anonymous,assetregister
