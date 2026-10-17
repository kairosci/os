local Blocks = {}

function Blocks.merge(content, first, last, body)
    assert(first ~= last and not first:find("\n", 1, true) and not last:find("\n", 1, true), "invalid_block_markers")
    local lines, inside = {}, false
    for line in (content:gsub("\n$", "") .. "\n"):gmatch("([^\n]*)\n") do
        if line == first then assert(not inside, "nested_managed_block"); inside = true
        elseif line == last then assert(inside, "unmatched_managed_block"); inside = false
        elseif not inside then lines[#lines + 1] = line end
    end
    assert(not inside, "unclosed_managed_block")
    while lines[#lines] == "" do table.remove(lines) end
    local prefix = #lines > 0 and table.concat(lines, "\n") .. "\n\n" or ""
    return prefix .. first .. "\n" .. body:gsub("\n$", "") .. "\n" .. last .. "\n"
end

function Blocks.remove(content, first, last)
    assert(first ~= last and not first:find("\n", 1, true) and not last:find("\n", 1, true), "invalid_block_markers")
    local lines, inside, found = {}, false, false
    for line in (content:gsub("\n$", "") .. "\n"):gmatch("([^\n]*)\n") do
        if line == first then assert(not inside, "nested_managed_block"); inside = true; found = true
        elseif line == last then assert(inside, "unmatched_managed_block"); inside = false
        elseif not inside then lines[#lines + 1] = line end
    end
    assert(not inside, "unclosed_managed_block")
    if not found then return nil end
    while lines[#lines] == "" do table.remove(lines) end
    return #lines > 0 and table.concat(lines, "\n") .. "\n" or ""
end

return Blocks
