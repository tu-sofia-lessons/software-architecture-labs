"""Tiny HTTP helpers over urllib (provided — the transport is not today's lesson).

They raise the normal urllib/socket errors:
  urllib.error.HTTPError  -- the server answered with 4xx/5xx (has .code). NOTE: subclass of URLError!
  urllib.error.URLError   -- could not connect (server down, wrong host)
  TimeoutError            -- no answer within `timeout` seconds
"""
import json
import urllib.request


def get_json(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def put_bytes(url, data, timeout):
    request = urllib.request.Request(url, data=data, method="PUT")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status
