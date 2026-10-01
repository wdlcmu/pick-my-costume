// Defensive redirect: the old browse surface is gone (no /browse* URL
// exists anywhere in the repo, verified 2026-10-01). Anything that reaches
// here gets a single 301 to /map/. Non-GET passes through untouched.
export async function onRequest(context) {
  if (context.request.method !== "GET") {
    return context.env.ASSETS.fetch(context.request);
  }
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    return context.env.ASSETS.fetch(context.request);
  }
  return Response.redirect(url.origin + "/map/" + url.search, 301);
}
