// Real ComfyUI workflow format. The preview sinks render text; no video model is loaded.
export function makeWorkflow(clips) {
  const nodes = [], links = [];
  clips.forEach((clip, index) => {
    const sourceId = index * 2 + 1, sinkId = sourceId + 1, linkId = index + 1;
    nodes.push({id: sourceId, type: "StoryboardClipPrompt", pos: [80, 80 + index * 260], size: [390, 180],
      flags: {}, order: index * 2, mode: 0, inputs: [],
      outputs: [{name: "prompt", type: "STRING", links: [linkId], slot_index: 0},
        {name: "duration_seconds", type: "FLOAT", links: null}, {name: "clip_id", type: "STRING", links: null}],
      title: `${clip.clip_id} · ${clip.duration}s · ${clip.target_model}`,
      properties: {"Node name for S&R": "StoryboardClipPrompt", storyboard: {board_id: clip.board_id,
        conversion_id: clip.conversion_id, clip_id: clip.clip_id, revision: clip.revision}},
      widgets_values: [JSON.stringify(clip)]});
    nodes.push({id: sinkId, type: "PreviewAny", pos: [570, 80 + index * 260], size: [420, 180],
      flags: {}, order: index * 2 + 1, mode: 0, inputs: [{name: "source", type: "*", link: linkId}],
      outputs: [{name: "STRING", type: "STRING", links: null}],
      properties: {"Node name for S&R": "PreviewAny"}, widgets_values: []});
    links.push([linkId, sourceId, 0, sinkId, 0, "STRING"]);
  });
  return {last_node_id: nodes.length, last_link_id: links.length, nodes, links, groups: [], config: {},
    extra: {storyboard_demo: "Authored sample. Saved prompt STRING outputs only; no AI or video generation."}, version: 0.4};
}
