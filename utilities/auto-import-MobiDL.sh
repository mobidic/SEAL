#!/usr/bin/env bash


path_seq="/RUNS/SEQUENCER/"
path_token="/SEAL/seal/static/temp/vcf/"
state_file="/SEAL/.seal_import_processed"
log_file="/SEAL/.seal_import.log"

# panel -> team id ; 0 = not imported ; panel not listed => not imported
declare -A panel_tid=(
    ["A"]=0
    ["B"]=9
)

default_callers="MD_DV:dv MD_HC:hc"

declare -A panel_callers=(
    ["B"]="MD_DV:dv MD_HC:hc MD_DS:ds"
)


scan_interval=3600   # scan 1 per hour
min_age=120 # cram stable

# -------------------------------------------------------------
build_basejson() {
    jq -n --arg sn "$1" --arg run_name "$2" --argjson tid "$3" \
       --arg vcf_path "$4" --arg cname "$5" --argjson add "$6" \
       '{samplename: $sn, run: {name: $run_name}, teams: [{id: $tid}],
         vcf_path: $vcf_path, caller: $cname, add_caller: $add}'
}

log() {
    echo "[$(date '+%F %T')] $*" >> "$log_file"
}

list_panels() {
    if dirs=( "${path_seq}"/"$1"/MobiDL/* ) && [[ -d ${dirs[0]} ]]; then
        ls -d "${path_seq}"/"$1"/MobiDL/*/* 2>/dev/null \
            | xargs -n1 basename \
            | sort -u
    fi    
}

max_run_age=7   # in days

list_recent_runs() {
    local cutoff
    cutoff=$(date -d "-${max_run_age} days" +%Y%m%d)

    ls -d "${path_seq}"2*/ 2>/dev/null \
        | xargs -n1 basename \
        | grep -E '^[0-9]{8}_' \
        | awk -v c="${cutoff}" '{d=substr($0,1,8); if (d >= c) print $0}'
}

scan() {
    while IFS= read -r run_name; do
        [ -z "$run_name" ] && continue
        log $run_name

        while IFS= read -r panel; do
            [ -z "$panel" ] && continue

            tid="${panel_tid[$panel]:-}"
            if [ -z "$tid" ]; then
                log "Panel $panel : ignored (unknown)"
                continue
            fi
            if [ "$tid" -eq 0 ]; then
                log "Panel $panel : ignored (tid = 0)"
                continue
            fi

            for cram in $(ls "${path_seq}"/"${run_name}"/MobiDL/*/"${panel}"/*/panelCapture/*.cram 2>/dev/null); do
                rel="${cram#"${path_seq}/${run_name}/MobiDL/"}"
                
                date_analysis=$(echo "$rel" | cut -d'/' -f1)
                panel_found=$(echo "$rel"   | cut -d'/' -f2)
                sample=$(echo "$rel"        | cut -d'/' -f3)
                lock_key="${run_name}-${panel_found}-${sample}"
                grep -qF "$lock_key" "$state_file" && continue

                mtime=$(stat -c %Y "$cram" 2>/dev/null) || continue
                now=$(date +%s)
                (( now - mtime < min_age )) && continue

                wf=$(dirname "$cram")
                sn=${sample}

                callers="${panel_callers[$panel]:-$default_callers}"
                count=1
                suffix=""
                add=false
                for spec in $callers; do
                    caller="${spec%%:*}"
                    ext="${spec##*:}"
                    token=$(build_basejson "$sn" "$run_name" "$tid" "$wf/$sn.${ext}.vcf" "${caller}" $add)
                    echo "$token" > "${path_token}/${run_name}-${tid}-${sn}-${count}-${ext}.token${suffix}"
                    add=true
                    let count++
                    suffix="2"
                done

                log "Import ${run_name}/${panel}/${sn} (team ${tid}, date ${date_analysis})"

                echo "$lock_key" >> "$state_file"
            done
        done < <(list_panels "$run_name")
    done < <(list_recent_runs)
}

mkdir -p "$(dirname "$state_file")" "$(dirname "$log_file")" "$path_token"
touch "$state_file"

log "=== SEAL auto-import MobiDL ==="
while true; do
    log "=== SCAN START ==="
    scan
    log "=== SCAN END ==="
    sleep "$scan_interval"
done