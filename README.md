# Skynet CDN Manager

![CICD Action](https://github.com/zerodaysec/skynet-cdn-manager/actions/workflows/cicd.yml/badge.svg)

![Skynet CDN Manager](https://cdn.n3rd-media.com/gfx/general/cdn.png)

This is a very simple (and I mean SIMPLE) streamlit app for managing files on s3 which I use as a CDN. This app allows
me to simply upload and download artifacts I store on my CDN. Mainly images but also some mp4s here and there.

## Assumptions

- This app needs an access key and secret defined in a `.env` file. Ive included a sample `.env.example` to get started.
- You need R/W on the buckets with `www` or `cdn` in their name as well as the ability to `list_buckets()`
