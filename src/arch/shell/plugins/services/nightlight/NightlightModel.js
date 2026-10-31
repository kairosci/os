function statusFromOutput(output) {
  try {
    var status = JSON.parse(String(output === undefined || output === null ? "" : output))
    if (typeof status.enabled !== "boolean") return null
    if (status.temperature !== null && (!Number.isInteger(status.temperature) || status.temperature < 0)) return null
    return { enabled: status.enabled, temperature: status.temperature }
  } catch (_) {
    return null
  }
}

if (typeof module !== "undefined") {
  module.exports = {
    statusFromOutput: statusFromOutput
  }
}
