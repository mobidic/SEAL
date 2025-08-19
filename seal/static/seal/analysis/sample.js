function toggle_status(id, status) {
    $.ajax({
        type: "POST",
        url: "/toggle/sample/status",
        data: {
            "sample_id": id,
            "status": status
        },
        success: function() {
            if (status == 1) {
                response = '<span class="w3-text-flat-peter-river"><i class="fas fa-user-clock"></i> <i><b>New Sample</b></i> <i class="fas fa-sort-down"></i></span>';
                $('.seal-form-report').removeClass('w3-disabled');
            } else if (status == 2) {
                response = '<span class="w3-text-flat-peter-river"><i class="fas fa-user-edit"></i> <i><b>Processing</b></i> <i class="fas fa-sort-down"></i></span>';
                $('.seal-form-report').removeClass('w3-disabled');
            } else if (status == 3) {
                response = '<span class="w3-text-flat-emerald"><i class="fas fa-user-check"></i> <i><b>Interpreted</b></i> <i class="fas fa-sort-down"></i></span>';
                $('.seal-form-report').removeClass('w3-disabled');
            } else if (status == 4) {
                response = '<span class="w3-text-flat-pumpkin"><i class="fas fa-user-lock"></i> <i><b>Validated</b></i> <i class="fas fa-sort-down"></i></span>';
                $('.seal-form-report').addClass('w3-disabled');
            }
            $('.button-status').html(response);
            $('#tableHistorySample').DataTable().ajax.reload();
        }
    });
}

const impact_dict = {
    "MODERATE": {
        "color": "orange",
        "score" : 2
    },
    "MODIFIER": {
        "color": "amethyst",
        "score" : 1.5
    },
    "HIGH": {
        "color": "alizarin",
        "score" : 3
    },
    "LOW": {
        "color": "turquoise",
        "score" : 1
    }
};


const consequences_dict = {
    "stop_gained": {
        "color": "e74c3c",
        "score": 50,
    },
    "stop_lost": {
        "color": "e74c3c",
        "score": 50,
    },
    "start_lost": {
        "color": "f39c12",
        "score": 30,
    },
    "splice_acceptor_variant": {
        "color": "d35400",
        "score": 20,
    },
    "splice_donor_variant": {
        "color": "d35400",
        "score": 20,
    },
    "frameshift_variant": {
        "color": "8e44ad",
        "score": 15,
    },
    "transcript_ablation": {
        "color": "e74c3c",
        "score": 8,
    },
    "transcript_amplification": {
        "color": "e44c7e",
        "score": 8,
    },
    "missense_variant": {
        "color": "f39c12",
        "score": 6,
    },
    "protein_altering_variant": {
        "color": "b086c0",
        "score": 5,
    },
    "splice_donor_5th_base_variant": {
        "color": "dd874d",
        "score": 5,
    },
    "splice_region_variant": {
        "color": "dd874d",
        "score": 5,
    },
    "splice_donor_region_variant": {
        "color": "dd874d",
        "score": 5,
    },
    "splice_polypyrimidine_tract_variant": {
        "color": "dd874d",
        "score": 5,
    },
    "inframe_insertion": {
        "color": "e44c7e",
        "score": 2,
    },
    "inframe_deletion": {
        "color": "e44c7e",
        "score": 2,
    },
    "incomplete_terminal_codon_variant": {
        "color": "9b59b6",
        "score": 2,
    },
    "stop_retained_variant": {
        "color": "27ae60",
        "score": 1,
    },
    "start_retained_variant": {
        "color": "27ae60",
        "score": 1,
    },
    "synonymous_variant": {
        "color": "27ae60",
        "score": 1,
    },
    "coding_sequence_variant": {
        "color": "16a085",
        "score": 0.75,
    },
    "mature_miRNA_variant": {
        "color": "16a085",
        "score": 0.5,
    },
    "intron_variant": {
        "color": "2980b9",
        "score": 0.25,
    },
    "NMD_transcript_variant": {
        "color": "eb796d",
        "score": 0.1,
    },
    "non_coding_transcript_exon_variant": {
        "color": "1abc9c",
        "score": 0.05,
    },
    "non_coding_transcript_variant": {
        "color": "1abc9c",
        "score": 0.005,
    },
    "coding_transcript_variant": {
        "color": "16a085",
        "score": 0.75,
    },
    "5_prime_UTR_variant": {
        "color": "62aee0",
        "score": 0.5,
    },
    "3_prime_UTR_variant": {
        "color": "62aee0",
        "score": 0.45,
    },
    "upstream_gene_variant": {
        "color": "83bfe7",
        "score": 0.0005,
    },
    "downstream_gene_variant": {
        "color": "83bfe7",
        "score": 0.0005,
    },
    "TFBS_ablation": {
        "color": "c0392b",
        "score": 0.00001,
    },
    "TFBS_amplification": {
        "color": "c0392b",
        "score": 0.00001,
    },
    "TF_binding_site_variant": {
        "color": "c0392b",
        "score": 0.00001,
    },
    "regulatory_region_ablation": {
        "color": "c0392b",
        "score": 0.005,
    },
    "regulatory_region_amplification": {
        "color": "c0392b",
        "score": 0.005,
    },
    "regulatory_region_variant": {
        "color": "c0392b",
        "score": 0.005,
    },
    "feature_elongation": {
        "color": "7f8c8d",
        "score": 0.00001,
    },
    "feature_truncation": {
        "color": "7f8c8d",
        "score": 0.0000001,
    },
    "intergenic_variant": {
        "color": "34495e",
        "score": 0.0000001,
    },
    "sequence_variant": {
        "color": "34495e",
        "score": 0.0000001,
    }
};

const class_variant_html = [
    '<span class="do-not-select"><i class="fas fa-ellipsis-h"></i></span>',
    '<span class="do-not-select w3-text-flat-green-sea"><span class="fa-layers fa-fw">'+
        '<i class="do-not-select fas fa-bookmark"></i>'+
        '<span class="do-not-select fa-layers-text fa-inverse" data-fa-transform="shrink-8 up-2" style="font-weight:900">1</span>'+
    '</span> - Benign</span>',
    '<span class="do-not-select w3-text-flat-nephritis"><span class="fa-layers fa-fw">'+
        '<i class="do-not-select fas fa-bookmark"></i>'+
        '<span class="do-not-select fa-layers-text fa-inverse" data-fa-transform="shrink-8 up-2" style="font-weight:900">2</span>'+
    '</span> - Likely Benign</span>',
    '<span class="do-not-select w3-text-flat-belize-hole"><span class="fa-layers fa-fw">'+
        '<i class="do-not-select fas fa-bookmark"></i>'+
        '<span class="do-not-select fa-layers-text fa-inverse" data-fa-transform="shrink-8 up-2" style="font-weight:900">3</span>'+
    '</span> - VUS</span>',
    '<span class="do-not-select w3-text-flat-pumpkin"><span class="fa-layers fa-fw">'+
        '<i class="do-not-select fas fa-bookmark"></i>'+
        '<span class="do-not-select fa-layers-text fa-inverse" data-fa-transform="shrink-8 up-2" style="font-weight:900">4</span>'+
    '</span> - Likely Pathogenic</span>',
    '<span class="do-not-select w3-text-flat-pomegranate"><span class="fa-layers fa-fw">'+
        '<i class="do-not-select fas fa-bookmark"></i>'+
        '<span class="do-not-select fa-layers-text fa-inverse" data-fa-transform="shrink-8 up-2" style="font-weight:900">5</span>'+
    '</span> - Pathogenic</span>',
];
const class_clinvar = [
    "0 - Benign/Likely Benign",
    "1 - Conflicting (without Pathogenic)",
    "2 - NA",
    "3 - Uncertain significance",
    "4 - Conflicting (with Pathogenic)",
    "5 - Pathogenic/Likely Pathogenic"
];
const reported_v = {
    true: "Reported"
};
const phenotypes = {
    "AD": "AD - Autosomal dominant",
    "AR": "AR - Autosomal recessive",
    "PD": "PD - Pseudoautosomal dominant",
    "PR": "PR - Pseudoautosomal recessive",
    "DD": "DD - Digenic dominant",
    "DR": "DR - Digenic recessive",
    "IC": "IC - Isolated cases",
    "ICB": "ICB - Inherited chromosomal imbalance",
    "Mi": "Mi - Mitochondrial",
    "Mu": "Mu - Multifactorial",
    "SMo": "SMo - Somatic mosaicism",
    "SMu": "SMu - Somatic mutation",
    "XL": "XL - X-linked",
    "XLD": "XLD - X-linked dominant",
    "XLR": "XLR - X-linked recessive",
    "YL": "YL - Y-linked"
};
const class_variant_export = {
    '0':'NA',
    '1':'1 - Benign',
    '2':'2 - Likely Benign',
    '3':'3 - VUS',
    '4':'4 - Likely Pathogenic',
    '5':'5 - Pathogenic',
};

function createBaseNList(number, n) {
    // return [...Array(number).keys()]
    return Array.from({ length: number }, (_, index) => index + n);
}

function getTextFromHTML(htmlString) {
    let temp = document.createElement('div');
    temp.innerHTML = htmlString;
    return temp.textContent || temp.innerText || '';
}

function BaseConditionsFilterSelect(values_options, condition="==", sort=true) {
    init = function (that, fn, preDefined = null) {
            that.dom.valueTitle.prop('selected', true);

            // // For "isTrue" or "isFalse", do not need select
            // if (condition === "isTrue" || condition === "isFalse") {
            //     let el = $()
            //         .addClass($.fn.dataTable.Criteria.classes.value);
            //     return el;
            // }

            // Declare select element to be used with all of the default classes and listeners.
            let el = $('<select/>')
                .addClass($.fn.dataTable.Criteria.classes.value)
                .addClass($.fn.dataTable.Criteria.classes.dropDown)
                .addClass($.fn.dataTable.Criteria.classes.italic)
                .addClass($.fn.dataTable.Criteria.classes.select)
                .append(that.dom.valueTitle)
                .on('change.dtsb', function() {
                    $(this).removeClass($.fn.dataTable.Criteria.classes.italic);
                    fn(that, this);
                });

            if (that.c.greyscale) {
                el.addClass($.fn.dataTable.Criteria.classes.greyscale);
            }

            let added = [];
            let options = [];

            // Function to add an option to the select element
            let addOption = (filt, text) => {
                if (that.s.type.includes('html') && filt !== null && typeof filt === 'string') {
                    filt.replace(/(<([^>]+)>)/ig, '');
                }

                // Add text and value, stripping out any html if that is the column type
                let opt = $('<option>', {
                    type: Array.isArray(filt) ? 'Array' : 'String',
                    value: filt
                })
                .data('sbv', filt)
                .addClass(that.classes.option)
                .addClass(that.classes.notItalic)
                // Have to add the text this way so that special html characters are not escaped - &amp; etc.
                .html(
                    typeof text === 'string' ?
                    text.replace(/(<([^>]+)>)/ig, '') :
                    text
                );

                let val = opt.val();

                // Check that this value has not already been added
                if (added.indexOf(val) === -1) {
                    added.push(val);
                    options.push(opt);

                    if (preDefined !== null && Array.isArray(preDefined[0])) {
                    preDefined[0] = preDefined[0].sort().join(',');
                    }

                    // If this value was previously selected as indicated by preDefined, then select it again
                    if (preDefined !== null && opt.val() === preDefined[0]) {
                    opt.prop('selected', true);
                    el.removeClass($.fn.dataTable.Criteria.classes.italic);
                    that.dom.valueTitle.removeProp('selected');
                    }
                }
            };
            for (i in values_options) {
                addOption(i, values_options[i]);
            }
            if (sort) {
                options.sort((a, b) => {
                    console.log(a.val())
                    if (a.val().toLowerCase() < b.val().toLowerCase()) {
                        return -1;
                    } else if (a.val().toLowerCase() > b.val().toLowerCase()) {
                        return 1;
                    } else {
                        return 0;
                    }
                });
            }

            for (let opt of options) {
                el.append(opt);
            }

            return el;
        };
    switch (condition) {
        case "==":
            conditionName ="Is"
            search = function (value, comparison) {
                v = value.split(",");
                return value == comparison[0];
            }
            break;
        case "!=":
            conditionName ="Is not"
            search = function (value, comparison) {
                return value != comparison[0];
            }
            break;
        case "contains":
            conditionName ="Contains"
            search = function (value, comparison) {
                v = value.split(",");
                return v.includes(comparison[0]);
            }
            break;
        case "!contains":
            conditionName ="Not Contains"
            search = function (value, comparison) {
                v = value.split(",");
                return ! v.includes(comparison[0]);
            }
            break;
        case "isTrue":
            conditionName = "Is True";
            search = function (value) {
                console.log("t");
                console.log((value === false ||
                       value === "false" ||
                       value === "0" ||
                       value === null ||
                       value === undefined ||
                       value === "" ||
                       (typeof value === 'number' && isNaN(value))))
                return value === true ||
                       value === "true" ||
                       value === "1" ||
                       (value !== null && value !== undefined && value !== "" && value !== "0" && value !== "false");
            };
            init = function(a){a.s.dt.one("draw.dtsb",function(){a.s.topGroup.trigger("dtsb-redrawLogic")})}
            break;
        case "isFalse":
            conditionName = "Is False";
            search = function (value) {
                console.log("f");
                console.log((value === false ||
                       value === "false" ||
                       value === "0" ||
                       value === null ||
                       value === undefined ||
                       value === "" ||
                       (typeof value === 'number' && isNaN(value))))
                return value === false ||
                       value === "false" ||
                       value === "0" ||
                       value === null ||
                       value === undefined ||
                       value === "" ||
                       (typeof value === 'number' && isNaN(value));
            };
            init = function(a){a.s.dt.one("draw.dtsb",function(){a.s.topGroup.trigger("dtsb-redrawLogic")})}
            break;
        default:
            conditionName = condition;
            search = function (value, comparison) {
                return false;
            };
    }
    return {
        conditionName: conditionName, // This is the string displayed in the condition select
        init: init,
        // This function gathers/sets the values from the dom elements created in the init function that are to be used for searching
        inputValue: function (el) {
            if (condition === "isTrue") {
                return ["isTrue"]; 
            }
            if (condition === "isFalse") {
                return ["isFalse"]; 
            }
            let values = [];

            for (let element of el) {
                if ($(element).is('select')) {
                    values.push($(element).children('option:selected').val());
                }
            }

            // return the selected values
            return values;
        },
        isInputValid: function (el, that) {
            // "isTrue" and "isFalse" : no need of values
            if (condition === "isTrue" || condition === "isFalse") {
                return true;
            }
            // If no options have been selected, or one has but it has no value then do not include the criteria
            if (
                $(el[0]).has('option:selected').length < 1 ||
                (
                    $(el[0]).has('option:selected').length === 1 &&
                    $($(el[0]).children('option:selected')[0]).text().length === 0
                )
            ) {
                return false;
            }

            return true;
        },
        // Straightforward search function comparing value from table and comparison from the select2 element
        // These values are retrieved in `inputValue`
        search: search,
        // Add a function to handle condition changes
        conditionChange: function(newCondition) {
            // When changing between no-value conditions, we need to trigger an update
            if ((condition === "isTrue" || condition === "isFalse") &&
                (newCondition === "isTrue" || newCondition === "isFalse")) {
                return true; // Indicate that an update is needed
            }
            return false;
        }
    }
}

function conditionsFilter(values_options, conditions=["==","!="], sort=true) {
    d = {}
    for (c of conditions) {
        d[c] = BaseConditionsFilterSelect(values_options,c, sort)
    }
    return d
}

function getIndexById(array, id, regexp=false) {
    if (regexp) {
        re = new RegExp(`${id}`)
        return array.map((elm, idx) => re.test(elm.id) ? idx : '').filter(String);
    }
    return array.findIndex(element => element.id === id);
}

function format_export (title) {
    return {
        header: function ( data, columnIdx ) {
            return (dt_table[columnIdx][title] !== undefined) ?  dt_table[columnIdx][title] : ((getTextFromHTML(data) === '' && dt_table[columnIdx]["id"] !== undefined) ?  dt_table[columnIdx]["id"] : getTextFromHTML(data));
        }
    }
}

// Define columns and format for export, filters...
columns_defGen = [
    getIndexById(dt_table, "export-filter-SYMBOL"),
    getIndexById(dt_table, "export-filter-HGVSc"),
    getIndexById(dt_table, "exportDefGen-HGVSp-short"),
    getIndexById(dt_table, "exportDefGen-HGVSc-short"),
    getIndexById(dt_table, "export-filter-Nearest"),
    getIndexById(dt_table, "export-filter-Transcript"),
    getIndexById(dt_table, "export-filter-COSMIC"),
    getIndexById(dt_table, "export-filter-RS"),
    getIndexById(dt_table, "export-filter-pos"),
    getIndexById(dt_table, "export-filter-consequences"),
    getIndexById(dt_table, "export-genome"),
    getIndexById(dt_table, "export-filter-chr"),
    getIndexById(dt_table, "export-filter-HGVSg"),
    getIndexById(dt_table, "export-filter-EI"),
    getIndexById(dt_table, "export-filter-AF")
]

columns_export = [
    getIndexById(dt_table, "^export-.*", true),
].flat()

columns_filter=[
    getIndexById(dt_table, "^(.*-){0,1}filter-.*", true),
].flat()

$(document).ready(function() {
    $.getJSON("/json/filters", function(data) {
        var options = "";
        for (x in data) {
            option = '<option value="' + x + '" '
            if (x == sample_filter_id) {
                option += 'selected>';
            } else {
                option += '>';
            }
            option += data[x]
            if (x == current_user_filter_id) {
                option += " (default)";
            }
            option += "</option>";
            options += option;
        }
        $('#selectFilter').html(options);
    });

    $.getJSON("/json/beds", function(data) {
        var options = '<option value="0">No panel</option>';
        for (x in data) {
            option = '<option value="' + x + '" '
            if (x == sample_bed_id) {
                option += 'selected>';
            } else {
                option += '>';
            }
            option += data[x]
            if (x == current_user_bed_id) {
                option += " (default)";
            }
            option += "</option>";
            options += option;
        }
        $('#selectBed').html(options);
    });
    table = $('#variants').DataTable({
        buttons:[],
        processing: true,
        language: {
            loadingRecords: '<div class="animation-bar-1"><span style="width:100%"></span></div>',
            processing: '<span><i class="fas fa-cog fa-spin"></i> Processing...</span>',
            searchBuilder: {
                button: {
                    0: 'Create filter',
                    _: 'Filter(s) (%d)'
                },
            },
            infoPostFix: " [Total variants: " + sample_variants_length + "]",
        },
        dom: 'Blfrti<"toolbar-variants">',
        scrollY:        "40vh",
        scrollX:        true,
        scrollCollapse: true,
        scroller:       true,
        fixedColumns: {
            left:2,
            right:1
        },
        'createdRow': function (row, data, rowIndex) {
            // Per-cell function to do whatever needed with cells
            $.each($('td', row), function (colIndex) {
                // For example, adding data-* attributes to the cell
                if (dt_table[colIndex]["mytitle"]) {
                    d2 = data;
                    if (dt_table[colIndex]["data"]) {
                        d2 = getValueFromHash(data, dt_table[colIndex]["data"]);
                    }
                    $(this).attr('title', dt_table[colIndex]["mytitle"](d2));
                }
                ;
            });
        },
        select: {
            style: 'multi',
            selector: 'td:not(:last-child)'

        },
        ajax: json_variants,
        columns: dt_table,
        initComplete: function(settings, json) {
            changeFilter(sample_filter_id, sample_id);
            if (sample_status != 4) {
                $('#selectFilter').prop('disabled', false);
                $('#selectBed').prop('disabled', false);
            }
            table.button().add( 0, {
                extend: 'collection',
                autoClose: true,
                text: 'Filter',
                className: 'custom-html-collection',
                buttons: [
                    {
                        extend: 'searchBuilder',
                        config: {
                            columns: columns_filter,
                            conditions: {
                                consequences: conditionsFilter(Object.keys(consequences_dict).reduce((acc, curr) => {acc[curr] = curr;return acc;}, {}), ["contains", "!contains"]),
                                impact: conditionsFilter(Object.keys(impact_dict).reduce((acc, curr) => {acc[curr] = curr;return acc;}, {}), ["==", "!="]),
                                clinvar: conditionsFilter(class_clinvar.reduce((acc, curr) => {acc[curr] = curr;return acc;}, {}), ["==", "!="]),
                                CLNREVSTAT: conditionsFilter(Object.keys(clinvar_stars).reduce((acc, curr) => {acc[curr] = `${curr} ${clinvar_stars[curr]}/4`;return acc;}, {}), ["==", "!="], false),
                                inheritances:  conditionsFilter(phenotypes, ["contains", "!contains"]),
                                class_seal:  conditionsFilter(class_variant_export, ["==", "!="]),
                                num: {"=":null, "!=": null},
                                reported:  conditionsFilter(reported_v, ["isTrue", "isFalse"]),

                            }
                        },
                    },
                    {
                        text: 'Save Filter',
                        action: function ( e, dt, node, config ) {
                            save_filters()
                        }
                    }, {
                        text: 'Update Filter',
                        action: function ( e, dt, node, config ) {
                            update_filter()
                        }
                    }
                ]
            } );
            table.button().add(1, {
                extend: 'collection',
                text: 'Export',
                autoClose: true,
                className: 'custom-html-collection',
                buttons: [
                    '<h3>All</h3>',
                    {
                        extend: 'copy',
                        text: 'Copy',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        },
                    },
                    {
                        extend: 'excel',
                        text: 'Excel',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'CSV',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'defGen',
                        title: '',
                        bom: false,
                        createEmptyCells: true,
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitleDefGen"),
                            modifier: {
                                selected: null
                            },
                            columns: columns_defGen
                        },
                        fieldSeparator: ";",
                        fieldBoundary: ''
                    },
                    '<h3>Reported</h3>',
                    {
                        extend: 'copy',
                        text: 'Copy',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            rows: [function(data, row, column, node) {
                                if(row.reported) {
                                    return data+1;
                                }
                            }],
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'excel',
                        text: 'Excel',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            rows: [function(data, row, column, node) {
                                if(row.reported) {
                                    return data+1;
                                }
                            }],
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'CSV',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: null
                            },
                            rows: [function(data, row, column, node) {
                                if(row.reported) {
                                    return data+1;
                                }
                            }],
                            modifier: {
                                selected: null
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'defGen',
                        title: '',
                        bom: false,
                        createEmptyCells: true,
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitleDefGen"),
                            modifier: {
                                selected: null
                            },
                            rows: [function(data, row, column, node) {
                                if(row.reported) {
                                    return data+1;
                                }
                            }],
                            columns: columns_defGen
                        },
                        fieldSeparator: ";",
                        fieldBoundary: ''
                    },
                    '<h3>Selected</h3>',
                    {
                        extend: 'copy',
                        text: 'Copy',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: true
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'excel',
                        text: 'Excel',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: true
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'CSV',
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitle"),
                            modifier: {
                                selected: true
                            },
                            columns: columns_export
                        }
                    },
                    {
                        extend: 'csv',
                        text: 'defGen',
                        title: '',
                        bom: false,
                        createEmptyCells: true,
                        exportOptions: {
                            orthogonal: 'export',
                            format: format_export("exportTitleDefGen"),
                            modifier: {
                                selected: true
                            },
                            columns: columns_defGen
                        },
                        fieldSeparator: ";",
                        fieldBoundary: ''
                    },
                ]
            });
            hide_message(count_hide);
        }
    });
    
 
	// $('a').on('click', function(e){
    //     e.preventDefault()
	// });
  
    table.on( 'user-select', function ( e, dt, type, cell, originalEvent ) {
        if ( originalEvent.target.classList.toString().match('do-not-select') ) {
            return false;
        }
    } );
    
} );

function hide_message(count_hide) {
    if (count_hide > 0) {
        $('.toolbar-variants').html('<span class="w3-text-flat-alizarin" style="margin-left:10px"><i class="fas fa-exclamation-triangle"></i> <span id="cpt-hide-row">' + count_hide + '</span> row(s) hidden (<b class="w3-hover-text-blue" onclick="showAllRows()" style="cursor:pointer">click here to show all</b>)<span>');
    } else {
        $('.toolbar-variants').html('');
    }
}

function hideRow(id_var, sample_id, item) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You will hide a variant",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, hide it!'
    }).then((result) => {
        if (result.isConfirmed) {
            $('#variants').DataTable()
                .row($(item).parents('tr'))
                .remove()
                .draw();
            var cpt = parseInt($('#cpt-hide-row').text()) || 0;
            hide_message(cpt+1);
            $.ajax({
                type: "POST",
                url: "/toggle/samples/variant/hide",
                data: {
                    id_var: id_var,
                    sample_id: sample_id
                },
                success: function() {
                    $('#tableHistorySample').DataTable().ajax.reload();
                }
            })
        }
    })
}

function showAllRows() {
    $('#variants').DataTable()
        .clear()
        .draw();
    $.ajax({
        type: "POST",
        url: "/toggle/samples/variant/hide/all",
        data: {
            sample_id: sample_id
        },
        success: function() {
            $('#tableHistorySample').DataTable().ajax.reload();
            $('#variants').DataTable().ajax.reload();
        }
    })
    hide_message(0);
}

function save_filters() {
    var d = table.searchBuilder.getDetails();
    $('#filterText').html(JSON.stringify(d));
    $('#filter-modal').toggle();
}

function update_filter() {
    var d = table.searchBuilder.getDetails();
    var id = $('#selectFilter').children(":selected").attr("value");
    if (id == 1) {
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: 'You cannot update default filter!',
            timer: 2000,
            showConfirmButton: false
          })
    } else {
        var t= $("#selectFilter option:selected").text();
        Swal.fire({
            title: 'Are you sure?',
            text: "You will update filter '" + t + "'.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, update it!'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire(
                    'Updated!',
                    "The filter '" + t + "' has been updated.",
                    'success'
                )
                $.ajax({
                    type: "POST",
                    url: "/add/filter",
                    data: {
                        id: id,
                        filter: JSON.stringify(d),
                        edit: true
                    }
                })
            }
        })
    }
}

function openHelp(title="Some help", content='Some Content', footer='') {
    Swal.fire({
        icon: 'question',
        title: title,
        html: '<div class="w3-left-align">'+ content + '</div>',
        footer: '<div class="w3-left-align">'+ footer + '</div>',
        width: 'max(50%, 400px)'
    })
}

function htmlLink(data) {
    return `<a class="w3-hover-text-${data.color}" href="${data.link_prefix}${data.id}${data.link_suffix}" target="_blank"><i class="w3-text-${data.color} ${data.flag}"></i> ${data.id}</a>`;
}

function openMD(id) {
    Swal.fire({
        title: 'Go to MobiDetails!',
        html: 'Please wait.<br/><b>This page will be close automatically.</b>',
        didOpen: () => {
            Swal.showLoading()
            $.ajax({
                type: 'POST',
                url: 'https://mobidetails.chu-montpellier.fr/api/variant/create',
                data: {
                    variant_chgvs: encodeURIComponent(id),
                    caller: 'cli',
                    api_key: current_user_api_key_md
                }
            })
            .done(function(data) {
                const b = Swal.getHtmlContainer().querySelector('b');
                if (! data.url) {
                    const b = Swal.getHtmlContainer().querySelector('b')
                    b.textContent = '<i class="fas fa-times-circle w3-text-flat-alizarin"></i> ' + data.mobidetails_error;
                } else {
                    b.textContent = `Redirection to ${data.url}`;
                    window.open(data.url);

                    // Swal.close()
                }
            });
        }
      })
}

function openDetailsVariantModal(id, sample_id) {
    request = "/json/variant/" + id + "/sample/" + sample_id;
    $.getJSON(request, function(data) {
        allTranscript = '<table class="table-modal-large w3-table-all w3-small w3-card" cellpadding="5" cellspacing="0" border="0">';
        allTranscript = allTranscript + '<thead class="w3-flat-silver"><tr>'+
            '<th class="w3-flat-silver control-size-100" >Gene</th>'+
            '<th class="w3-flat-silver control-size-200">Transcript</th>'+
            '<th class="w3-flat-silver control-size-150">Biotype</th>'+
            '<th class="w3-flat-silver control-size-100">Canonical</th>'+
            '<th class="w3-flat-silver control-size-150" title="Exon-Intron">Ex-In</th>'+
            '<th class="w3-flat-silver control-size-300" >HGVSc</th>'+
            '<th class="w3-flat-silver control-size-300" >HGVSp</th>'+
            '<th class="w3-flat-silver size-250">Consequences</th>'+
            '<th class="showTitle w3-flat-silver control-size-100">MES ref</th>'+
            '<th class="showTitle w3-flat-silver control-size-100">MES diff</th>'+
            '<th class="showTitle w3-flat-silver control-size-100">MES alt</th>'+
        '</tr></thead>';
        allTranscript = allTranscript + '<tbody>';

        var allScoresPredictions = {
            "SIFT_converted_rankscore": null,
            "SIFT4G_converted_rankscore": null,
            "Polyphen2_HDIV_rankscore": null,
            "Polyphen2_HVAR_rankscore": null,
            "PROVEAN_converted_rankscore": null,
            "LRT_converted_rankscore": null,
            "MutationTaster_converted_rankscore": null,
            "MutationAssessor_rankscore": null,
            "FATHMM_converted_rankscore": null,
            "fathmm-MKL_coding_rankscore": null,
            "fathmm-XF_coding_rankscore": null,
            "CADD_raw_rankscore": null,
            "CADD_raw_rankscore_hg19": null,
            "VEST4_rankscore": null,
            "integrated_fitCons_rankscore": null,
            "GM12878_fitCons_rankscore": null,
            "H1-hESC_fitCons_rankscore": null,
            "HUVEC_fitCons_rankscore": null,
            "LINSIGHT_rankscore": null,
            "DANN_rankscore": null,
            "MetaSVM_rankscore": null,
            "MetaLR_rankscore": null,
            "GenoCanyon_rankscore": null,
            "Eigen-raw_coding_rankscore": null,
            "Eigen-PC-raw_coding_rankscore": null,
            "M-CAP_rankscore": null,
            "REVEL_rankscore": null,
            "MutPred_rankscore": null,
            "MVP_rankscore": null,
            "MPC_rankscore": null,
            "PrimateAI_rankscore": null,
            "DEOGEN2_rankscore": null,
            "BayesDel_addAF_rankscore": null,
            "BayesDel_noAF_rankscore": null,
            "ClinPred_rankscore": null,
            "LIST-S2_rankscore": null
        }

        var allScoresConservation = {
            "bStatistic_converted_rankscore": null,
            "phyloP100way_vertebrate_rankscore": null,
            "phyloP30way_mammalian_rankscore": null,
            "phyloP17way_primate_rankscore": null,
            "phastCons100way_vertebrate_rankscore": null,
            "phastCons30way_mammalian_rankscore": null,
            "phastCons17way_primate_rankscore": null,
            "GERP++_RS_rankscore": null,
            "SiPhy_29way_logOdds_rankscore": null
        }

        var allScoresPopulation = {
            "gnomADg_AF": null,
            "gnomADg_AF_AFR": null,
            "gnomADg_AF_AMR": null,
            "gnomADg_AF_ASJ": null,
            "gnomADg_AF_EAS": null,
            "gnomADg_AF_FIN": null,
            "gnomADg_AF_NFE": null,
            "gnomADg_AF_OTH": null
        }

        var MaxEntScan_alt = null;
        var MaxEntScan_ref = null;
        var MaxEntScan_ratio = null;

        var spliceAI = {
            "AG": {
                "score": null,
                "pos": null,
                "name": "Acceptor Gain"
            },
            "DG": {
                "score": null,
                "pos": null,
                "name": "Donor Gain"
            },
            "AL": {
                "score": null,
                "pos": null,
                "name": "Acceptor Loss"
            },
            "DL": {
                "score": null,
                "pos": null,
                "name": "Donor Loss"
            }
        }
        for (x in data["annotations"]["ANN"]) {

            var links = []
            for (idx_var in data["annotations"]["ANN"][x]["Existing_variation"]) {
                id_var = data["annotations"]["ANN"][x]["Existing_variation"][idx_var]
                if (RegExp("^rs[0-9]+").test(id_var)) {
                    let dbsnp = {
                        link_prefix: "https://www.ncbi.nlm.nih.gov/snp/",
                        id: id_var,
                        link_suffix: "",
                        color: "flat-asbestos",
                        flag: "fas fa-flag"
                    }
                    links.push(htmlLink(dbsnp))
                }
            }
            for (idx_var in data["annotations"]["ANN"][x]["VAR_SYNONYMS"]) {
                let var_synonyms = {
                    link_prefix: "",
                    id: "",
                    link_suffix: "",
                    color: "",
                    flag: null
                }
                if (idx_var == "ClinVar") {
                    var_synonyms.color = "flat-belize-hole"
                    var_synonyms.flag = "fas fa-user-md"
                    var_synonyms.clinvar = true
                } else if (idx_var == "UniProt") {
                    var_synonyms.link_prefix = "https://web.expasy.org/variant_pages/"
                    var_synonyms.link_suffix = ".html"
                    var_synonyms.color = "flat-pomegranate"
                    var_synonyms.flag = "fas fa-microscope"
                } else if (idx_var == "COSMIC") {
                    var_synonyms.link_prefix = "https://cancer.sanger.ac.uk/cosmic/search?genome=37&q="
                    var_synonyms.color = "flat-amethyst"
                    var_synonyms.flag = "fas fa-disease"
                }
                if (var_synonyms.flag != null) {
                    for (idx_var2 in data["annotations"]["ANN"][x]["VAR_SYNONYMS"][idx_var]) {
                        var_synonyms.id = data["annotations"]["ANN"][x]["VAR_SYNONYMS"][idx_var][idx_var2]
                        if (var_synonyms.clinvar) {
                            if (RegExp("^VCV[0-9]+").test(var_synonyms.id)) {
                                var_synonyms.link_prefix = "https://www.ncbi.nlm.nih.gov/clinvar/variation/"
                            } else {
                                var_synonyms.link_prefix = "https://www.ncbi.nlm.nih.gov/clinvar/"
                            }
                        }
                        links.push(htmlLink(var_synonyms))
                    }
                }

            }

            for (idx_var in data["annotations"]["ANN"][x]["PUBMED"]) {
                id_var = data["annotations"]["ANN"][x]["PUBMED"][idx_var]
                let pubmed = {
                    link_prefix: "https://pubmed.ncbi.nlm.nih.gov/",
                    id: id_var,
                    link_suffix: "",
                    color: "flat-wet-asphalt",
                    flag: "fas fa-book"
                }
                links.push(htmlLink(pubmed))
            }

            $("#links_exterior").html(links.join("<br />"));

            cell = "";
            for (idx in consequences_dict) {
                if (data["annotations"]["ANN"][x]["Consequence"].includes(idx)){
                    color = idx in consequences_dict ? consequences_dict[idx]["color"] : "7f8c8d";
                    style = "style='max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;background-color:#" + color + ";'";
                    cell += " <span class='w3-tag' " + style + ">" + idx + "</span>"
                }
            }
            color = "";
            if (current_user_transcripts.includes(data["annotations"]["ANN"][x]["Feature"])) {
                color = "w3-text-flat-peter-river";
            }
            if (data["annotations"]["ANN"][x]["canonical"]) {
                response = '<i title="CANONICAL" class="' + color + ' fas fa-star"></i>';
            } else {
                response = '<i title="" class="' + color + ' far fa-star"></i>';
            }
            mobidetails="";
            if (data["annotations"]["ANN"][x]["HGVSc"] != null && data["annotations"]["ANN"][x]["HGVSc"].substr(0,3) == 'NM_') {
                if (current_user_api_key_md) {
                    mobidetails = '<span onclick="openMD(\'' + data["annotations"]["ANN"][x]["HGVSc"] + '\')" class="fa-layers fa-fw w3-text-flat-peter-river w3-hover-text-flat-carrot" style="cursor: pointer;"> <i class="fas fa-bookmark"></i> <span class="fa-layers-text fa-inverse" data-fa-transform="shrink-10 up-2" style="font-weight:900">MD</span></span> '
                }
            }
            hgvsc = mobidetails + data["annotations"]["ANN"][x]["HGVSc"];
            allTranscript = allTranscript + '<tr>'+
                '<td class="w3-text-black showTitle control-size-100" >'+data["annotations"]["ANN"][x]["SYMBOL"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-200" >'+data["annotations"]["ANN"][x]["Feature"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-150" >'+data["annotations"]["ANN"][x]["BIOTYPE"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-100 w3-center" >'+response+'</td>'+
                '<td class="w3-text-black showTitle control-size-150" >'+data["annotations"]["ANN"][x]["EI"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-300" >'+hgvsc+'</td>'+
                '<td class="w3-text-black showTitle control-size-300" >'+data["annotations"]["ANN"][x]["HGVSp"]+'</td>'+
                '<td class="w3-text-black showTitle size-250">'+cell+'</td>'+
                '<td class="w3-text-black showTitle control-size-100">'+data["annotations"]["ANN"][x]["MaxEntScan_ref"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-100">'+data["annotations"]["ANN"][x]["MaxEntScan_diff"]+'</td>'+
                '<td class="w3-text-black showTitle control-size-100">'+data["annotations"]["ANN"][x]["MaxEntScan_alt"]+'</td>'+
            '</tr>';

            for (nameScore in allScoresPredictions) {
                if (data["annotations"]["ANN"][x][nameScore] != null) {
                    allScoresPredictions[nameScore] = Math.max(data["annotations"]["ANN"][x][nameScore], allScoresPredictions[nameScore]);
                }
            };

            for (nameScore in allScoresConservation) {
                if (data["annotations"]["ANN"][x][nameScore] != null) {
                    allScoresConservation[nameScore] = Math.max(data["annotations"]["ANN"][x][nameScore], allScoresConservation[nameScore]);
                }
            };

            for (nameScore in allScoresPopulation) {
                if (data["annotations"]["ANN"][x][nameScore] != null) {
                    allScoresPopulation[nameScore] = Math.max(data["annotations"]["ANN"][x][nameScore], allScoresPopulation[nameScore]);
                }
            };
            if (data["annotations"]["ANN"][x]["MaxEntScan_ref"] != null && data["annotations"]["ANN"][x]["MaxEntScan_alt"] != null) {
                MES_ref = Math.abs(data["annotations"]["ANN"][x]["MaxEntScan_ref"]);
                MES_alt = Math.abs(data["annotations"]["ANN"][x]["MaxEntScan_alt"]);
                MES_ratio = -100 + (MES_alt*100) / MES_ref;
                if (Math.abs(MES_ratio) > Math.abs(MaxEntScan_ratio)) {
                    MaxEntScan_ratio = MES_ratio;
                    MaxEntScan_ref = data["annotations"]["ANN"][x]["MaxEntScan_ref"];
                    MaxEntScan_alt = data["annotations"]["ANN"][x]["MaxEntScan_alt"];
                }
            };

            for (site in spliceAI) {
                var keyScore = "SpliceAI_pred_DS_" + site;
                var keyPos = "SpliceAI_pred_DP_" + site;
                var score = data["annotations"]["ANN"][x][keyScore];
                var pos = data["annotations"]["ANN"][x][keyPos];
                if (score != null && score >= spliceAI[site]["score"]) {
                    spliceAI[site]["score"] = score;
                    spliceAI[site]["position"] = pos;
                }
            }
        }
        allTranscript = allTranscript + '</tbody>';
        allTranscript = allTranscript + '</table>';
        $("#allTranscriptsTable").html(allTranscript);


        inSeal = '<table class="table-modal-large w3-table-all w3-small w3-card" cellpadding="5" cellspacing="0" border="0">';
        inSeal = inSeal + '<thead class="w3-flat-silver"><tr>'+
            '<th class="w3-flat-silver control-size-100">Sample</th>'+
            '<th class="w3-flat-silver control-size-100">Family</th>'+
            '<th class="w3-flat-silver control-size-100">Teams</th>'+
            '<th class="w3-flat-silver control-size-75 w3-center">Affected</th>'+
            '<th class="w3-flat-silver control-size-75 w3-center">Depth</th>'+
            '<th class="w3-flat-silver control-size-100 w3-center">Allelic Depth</th>'+
            '<th class="w3-flat-silver control-size-100 w3-center">Allelic frequencie</th>'+
            '<th class="w3-flat-silver control-size-100 w3-center">Reported</th>'+
        '</tr></thead>';
        inSeal = inSeal + '<tbody>';

        var count = 0;
        for (x in data["samples"]) {
            if (data["samples"][x]["reported"]) {
                reported = '<span class="w3-tag w3-round w3-flat-nephritis"><i title="Reported" class="fas fa-check-circle"></i></span>'
            } else {
                reported = '<span class="w3-tag w3-round w3-dark-gray"><i title="Not Reported" class="fas fa-times-circle"></i></span>'
            }
            if (data["samples"][x]["affected"]) {
                affected = '<span class="w3-tag w3-round w3-flat-pomegranate"><i title="Affected" class="fas fa-user-check"></i></span>'
            } else {
                affected = '<span class="w3-tag w3-round w3-dark-grey"><i title="Not Affected" class="fas fa-user-times"></i></span>'
            }
            if (data["samples"][x]["current_family"]) {
                family = '<b><span class="w3-tag w3-round w3-flat-nephritis">' + data["samples"][x]["family"] + '</span></b>';
                sample = '<b><span class="w3-tag w3-round w3-flat-nephritis">' + data["samples"][x]["samplename"] + '</span></b>';
            } else {
                family = data["samples"][x]["family"];
                sample = data["samples"][x]["samplename"];
            }
            style=""
            if (data["samples"][x]["current"]) {
                sample = '<b><span class="w3-tag w3-round w3-flat-nephritis">' + data["samples"][x]["samplename"] + '</span></b>';
                style =  "style='background-color:#85b3d5'"
            }
            teams=""
            for (i in data["samples"][x]["teams"]) {
                teams += '<span class="w3-tag" style="max-width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;background-color:' + data["samples"][x]["teams"][i]["color"] + '">' + data["samples"][x]["teams"][i]["teamname"] + '</span> ';
            };
            inSeal = inSeal + '<tr>'+
                '<td class="control-size-100" ' + style + '>' + sample + '</td>'+
                '<td class="control-size-100" ' + style + '>' + family+ '</td>'+
                '<td class="control-size-100" ' + style + '>' + teams + '</td>'+
                '<td class="control-size-75 w3-center" ' + style + '>' + affected + '</td>'+
                '<td class="control-size-75 w3-center" ' + style + '>' + data["samples"][x]["depth"] + '</td>'+
                '<td class="control-size-100 w3-center" ' + style + '>' + data["samples"][x]["allelic_depth"] + '</td>'+
                '<td class="control-size-100 w3-center" ' + style + '>' + data["samples"][x]["allelic_frequency"] + '</td>'+
                '<td class="control-size-100 w3-center" ' + style + '>' + reported + '</td>'+
            '</tr>'
            count += 1;
        }

        inSeal = inSeal + '</tbody>';
        inSeal = inSeal + '</table>';
        $("#inSEALTable").html(inSeal);
        $('.table-modal-large').DataTable( {
            scrollY:        '50vh',
            scrollX:        true,
            paging:         false
        });
        $('.inSealCount').html(count);

        tableScoresPredictions = '<table class="table-modal w3-table-all w3-tiny w3-card" cellpadding="5" cellspacing="0" border="0" style="width:100%">';
        tableScoresPredictions = tableScoresPredictions + '<thead class="w3-flat-silver"><tr>'+
            '<th class="w3-flat-silver">Name</th>'+
            '<th class="w3-flat-silver">Score</th>'+
        '</tr></thead>';
        tableScoresPredictions = tableScoresPredictions + '<tbody>';
        for (nameScore in allScoresPredictions) {
            tableScoresPredictions = tableScoresPredictions + '<tr>'+
                '<td class="w3-text-black showTitle">'+nameScore+'</td>'+
                '<td class="w3-text-black showTitle">'+allScoresPredictions[nameScore]+'</td>'+
            '</tr>';
        };
        tableScoresPredictions = tableScoresPredictions + '</tbody>';
        tableScoresPredictions = tableScoresPredictions + '</table>';
        $("#tableScoresPredictions").html(tableScoresPredictions);

        tableScoresConservation = '<table class="table-modal w3-table-all w3-tiny w3-card" cellpadding="5" cellspacing="0" border="0">';
        tableScoresConservation = tableScoresConservation + '<thead class="w3-flat-silver"><tr>'+
            '<th class="w3-flat-silver">Name</th>'+
            '<th class="w3-flat-silver">Score</th>'+
        '</tr></thead>';
        tableScoresConservation = tableScoresConservation + '<tbody>';
        for (nameScore in allScoresConservation) {
            tableScoresConservation = tableScoresConservation + '<tr>'+
                '<td class="w3-text-black showTitle">'+nameScore+'</td>'+
                '<td class="w3-text-black showTitle">'+allScoresConservation[nameScore]+'</td>'+
            '</tr>';
        };
        tableScoresConservation = tableScoresConservation + '</tbody>';
        tableScoresConservation = tableScoresConservation + '</table>';
        $("#tableScoresConservation").html(tableScoresConservation);

        $('.table-modal').DataTable();

        wi1 = window.screen.width;
        var apply = 433.983;
        if (wi1 <= 768) {
            apply = 467.983;
        } else if (wi1 <= 992) {
            apply = 567.983;
        }


        var radarData = [];
        var radarLabels = [];
        for (nameScore in allScoresPredictions) {
            if (allScoresPredictions[nameScore] != null) {
                radarData.push(allScoresPredictions[nameScore]);
                radarLabels.push(nameScore.replace(/_rankscore$/gm,''));
            }
        };
        radarData.push(radarData[0]);
        radarLabels.push(radarLabels[0]);
        var data_missense = [{
            type: 'scatterpolar',
            r: [
                Math.max(allScoresPredictions["CADD_raw_rankscore"], 0),
                Math.max(allScoresPredictions["VEST4_rankscore"], 0),
                Math.max(allScoresPredictions["MetaSVM_rankscore"], 0),
                Math.max(allScoresPredictions["MetaLR_rankscore"], 0),
                Math.max(allScoresPredictions["Eigen-raw_coding_rankscore"], 0),
                Math.max(allScoresPredictions["Eigen-PC-raw_coding_rankscore"], 0),
                Math.max(allScoresPredictions["REVEL_rankscore"], 0),
                Math.max(allScoresPredictions["BayesDel_addAF_rankscore"], 0),
                Math.max(allScoresPredictions["BayesDel_noAF_rankscore"], 0),
                Math.max(allScoresPredictions["ClinPred_rankscore"], 0),
                Math.max(allScoresPredictions["CADD_raw_rankscore"], 0),
            ],
            theta: [
                "CADD",
                "VEST4",
                "MetaSVM",
                "MetaLR",
                "Eigen",
                "Eigen_PC",
                "REVEL",
                "BayesDel_addAF",
                "BayesDel_noAF",
                "ClinPred",
                "CADD"
            ],
            fill: 'toself'
        }]

        var layout_radar = {
            width: apply,
            polar: {
                radialaxis: {
                    visible: true,
                    range: [0, 1]
                }
            },
            showlegend: false
        }

        var radarData = [];
        var radarLabels = [];
        for (nameScore in allScoresConservation) {
            radarData.push(Math.max(allScoresConservation[nameScore], 0));
            radarLabels.push(nameScore.replace(/_rankscore$/gm,''));
        };
        radarData.push(radarData[0]);
        radarLabels.push(radarLabels[0]);

        var data_cons = [{
            type: 'scatterpolar',
            r: radarData,
            theta: radarLabels,
            fill: 'toself'
        }]
        var config = {responsive: true}

        Plotly.newPlot("radarMissense", data_missense, layout_radar, config)
        Plotly.newPlot("radarConservation", data_cons, layout_radar, config)

        gnomad = '<a target="_blank" href="https://gnomad.broadinstitute.org/variant/' + id + '" class="w3-text-blue w3-hover-text-indigo" style="cursor: pointer;">GnomAD</a> ';
        $("#population h3").html("Population (" + gnomad + ")");

        var gnomad_data = [];
        var gnomad_labels = [];
        for (nameScore in allScoresPopulation) {
            gnomad_data.push(Math.max(allScoresPopulation[nameScore], 0));
            gnomad_labels.push(nameScore.replace(/_rankscore$|^gnomADg_|AF_/gm,'').replace(/^AF$/gm,'ALL'));
        };

        var data_gnomad = [
            {
                x: gnomad_labels,
                y: gnomad_data,
                type: 'bar',
                text: gnomad_data.map(function (k) { if (k && k< 0.01) { return k.toExponential(2); } else if(k){return k.toFixed(4);} else {return 'NA'}}),
                textposition:'outside',
                textfont: {
                    size: 14,
                },
                width: 0.15,
                constraintext: 'none',
            }
        ];

        layout_bar = {
            hovermode: false,
            width: $("#modal-details-variant div header").width(),
            margin: {
              l: 50,
              r: 0,
              b: 50,
              t: 0,
              pad: 4
            },
            yaxis: {fixedrange: true},
            xaxis : {fixedrange: true}
        }
        Plotly.newPlot('barPopulation', data_gnomad, layout_bar, config);

        var traceMES = {
            x: ['Ref', 'Alt'],
            y: [MaxEntScan_ref, MaxEntScan_alt],
            text: [MaxEntScan_ref, MaxEntScan_alt],
            name: "",
            marker:{
                color: ['#3498db', '#34495e']
            },
            type: 'bar',
            hovertemplate: "<b>MES %{x} : %{y:.0f}</b>"
        };

        var traceSpliceAI = []
        var max=1;
        for (site in spliceAI) {
            var min = max - 0.15;
            var color = "#7f8c8d";
            if (spliceAI[site]["score"] >= 0.8) {
                color = "#e74c3c";
            } else if (spliceAI[site]["score"] >= 0.5) {
                color = "#e67e22";
            } else if (spliceAI[site]["score"] >= 0.2) {
                color = "#f1c40f";
            }
            var trace = {
                domain: { x: [0.35, 1], y: [min, max] },
                type: "indicator",
                mode: "number+gauge",
                gauge: {
                    shape: "bullet",
                    text:"t",
                    axis: { range: [null, 1] },
                    threshold: {
                        line: { color: "#e74c3c", width: 1 },
                        thickness: 0.75,
                        value: 0.8
                    },
                    steps: [
                        { range: [0, 0.5], color: "#ecf0f1" },
                        { range: [0, 0.2], color: "#bdc3c7" },
                    ],
                    bar: {thickness:0.5, color: color },
                },
                value: spliceAI[site]["score"],
                title: {
                    text:
                    "<b>" + spliceAI[site]["name"] + "</b><br><span style='color: gray; font-size:0.8em'>" + spliceAI[site]["position"] + "</span>",
                    font: { size: 14 }
                },
            };
            traceSpliceAI.push(trace);
            max = min - 0.13
        }

        var data1 = [traceMES];
        data1 = data1.concat(traceSpliceAI);
        var layout = {
            width: apply*2,
            showlegend: false,
            xaxis: {
            domain: [0, 0.15],
            anchor: 'y1'
        },title: "Splicing prediction scores (MaxEntScan & spliceAI)",
            yaxis: {
            domain: [0, 1],
            anchor: 'x1'
            },
        };

        Plotly.newPlot('chartSplicing', data1, layout);

        comments = '<table id="tableCommentsVar" class="w3-table-all w3-small w3-card" cellpadding="5" cellspacing="0" border="0" style="width:100%">';
        comments = comments + '<thead class="w3-flat-silver"><tr>'+
            '<th class="w3-flat-silver no-sort" style="width:100px;min-width:100px;max-width:100px;">User</th>'+
            '<th class="w3-flat-silver no-sort" style="width:462px;min-width:462px;max-width:462px;">Comment</th>'+
            '<th class="w3-flat-silver" style="width:200px;min-width:200px;max-width:200px;">Date</th>'+
        '</tr></thead>';
        comments = comments + '<tbody>';

        var count = 0;
        for (x in data["comments"]) {
            comments = comments + '<tr>'+
                '<td>' + data["comments"][x]["user"] + '</td>'+
                '<td>' + data["comments"][x]["comment"] + '</td>'+
                '<td>' + data["comments"][x]["date"] + '</td>'+
            '</tr>';
            count+=1;
        }

        comments = comments + '</tbody>';
        comments = comments + '</table>';
        $("#commentsTableVar").html(comments);
        $('.commentsCountVar').html(count);

        $('#tableCommentsVar').DataTable({
            searching:false,
            lengthMenu: [ 10 ],
            dom: 'tip',
            order: [[ 2, "desc" ]],
            columnDefs: [
                    {
                        orderable: false,
                        targets:  "no-sort"
                    }
                ],
        });
    });
    $("#variant-id").html(id);
    $('#modal-details-variant').toggle()
}


document.getElementsByClassName("tablink")[0].click();

function openDetails(evt, detailName) {
    var i, x, tablinks;
    $('.detail').hide();
    $('.tablink').removeClass('w3-flat-turquoise');
    $('#' + detailName).show();
    evt.currentTarget.classList.add("w3-flat-turquoise");
}

function changeFilter(id=1, sample_id) {
    id = id != "None" ? id : 1;
    $.getJSON("/json/filter/" + id, function(data) {
        document.getElementById("variants_processing").style.visibility = "visible";
        document.getElementById("variants_processing").style.zIndex = "10";
        $("#variants_processing").toggle();
        document.getElementById("variants").style.opacity = "0.5";
        setTimeout(function () {
            table.searchBuilder.rebuild(data);
            document.getElementById("variants_processing").style.visibility = "hidden";
            document.getElementById("variants_processing").style.zIndex = "0";
            $("#variants_processing").toggle();
            document.getElementById("variants").style.opacity = "1";
            $.ajax({
                type: "POST",
                url: "/toggle/sample/filter",
                data: {
                    "id_sample": sample_id,
                    "id_filter": id
                },
                success: function() {
                    $('#tableHistorySample').DataTable().ajax.reload();
                    table.order([2, "asc"]).draw();
                }
            });
        }, 30);
    });
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == document.getElementById('modal-details-variant')) {
        $('#modal-details-variant').toggle();
    }
    if (event.target == document.getElementById('help-modal')) {
        $('#help-modal').toggle();
    }
    if (event.target == document.getElementById('filter-modal')) {
        $('#filter-modal').toggle();
    }
    if (event.target == document.getElementById('MD-message-modal')) {
        $('#MD-message-modal').toggle();
    }
}

$("#edit-name").keyup(function(event) {
    if (event.keyCode === 13) {
        edit_name()
    }
});

function edit_name() {
    Swal.fire({
        title: 'Are you sure?',
        text: "You will rename the sample.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, rename it!'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire(
                'Renamed!',
                'The sample will be renamed.',
                'success'
            )
            $.ajax({
                type: "POST",
                url: "/edit/sample/name",
                data: {
                    "sample_id": sample_id,
                    "new_name": $('#edit-name').val()
                },
                success: function() {
                    $( "#error-message-edit-name" ).remove();
                    $("h1").html(DOMPurify.sanitize($('#edit-name').val()));
                    $('#tableHistorySample').DataTable().ajax.reload();
                },
                error: function(XMLHttpRequest) {
                    $( "#error-message-edit-name" ).remove();
                    msg = "<p id='error-message-edit-name' class='w3-small w3-text-flat-alizarin' style='margin:0px'><i class='fas fa-exclamation-circle'></i> " + XMLHttpRequest["responseJSON"]["message"] + "</p>"
                    $( "#sample-name-sidebar" ).after( msg );
                }
            })
        }
    })
}

function toggle_class(id_var, sample_id, class_variant, self) {
    $.ajax({
        type: "POST",
        url: "/toggle/samples/variant/class",
        data: {
            "id_var": id_var,
            "sample_id": sample_id,
            "class_variant": class_variant
        },
        success: function() {
            var cell = $('#variants').DataTable().cell(self.closest('td'))
            cell.data(class_variant).draw();
            // CREATE SWEET ALERT
        }
    })
}

function toggle_on_off(div) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You will change sample status: switch '" + div + "' status.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, edit it!'
      }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire(
                'Edited!',
                "The sample status '" + div + "' switched.",
                'success'
            )
            $.ajax({
                type: "POST",
                url: "/toggle/sample/" + div,
                data: {
                    "sample_id": sample_id
                },
                success: function() {
                    $("#toggle-" + div).toggleClass(["fa-toggle-on", "fa-toggle-off", "w3-text-flat-green-sea"]);
                    $('#tableHistorySample').DataTable().ajax.reload();
                }
            })
        }
      })
}

function toggle_var2sample_status(id, id_var, sample_id, type, self) {
    $.ajax({
        type: "POST",
        url: "/toggle/samples/variant/status",
        data: {
            "id_var": id_var, "sample_id": sample_id, "type":type
        },
        success: function() {
            $('#tableHistorySample').DataTable().ajax.reload();
            var cell = $('#variants').DataTable().cell(self.closest('td'))
            var data = cell.data();
            data["reported"]=!cell.data()["reported"];
            cell.data(data).draw();
        }
    })
}

function send_comment(type="sample") {
    if( type == "var") {
        var comment = $("#commentVar").val();
        var id = $("#variant-id").text();
        var url = "/add/comment/variant";
    }
    if( type == "sample") {
        var comment = $("#comment_sample").val();
        var id = sample_id;
        var url = "/add/comment/sample";
    }
    $.ajax({
        type: "POST",
        url: url,
        data: {
            "id": id, "comment": encodeURI(comment)
        }
    }).done(function() {
        if (type=="var") {
            $("#commentVar").val("");
            $.getJSON("/json/variant/" + id, function(data) {
                comments = '<table id="tableCommentsVar" class="w3-table-all w3-small w3-card" cellpadding="5" cellspacing="0" border="0" style="width:100%">';
                comments = comments + '<thead class="w3-flat-silver"><tr>'+
                    '<th class="w3-flat-silver no-sort" style="width:100px;min-width:100px;max-width:100px;">User</th>'+
                    '<th class="w3-flat-silver no-sort" style="width:462px;min-width:462px;max-width:462px;">Comment</th>'+
                    '<th class="w3-flat-silver" style="width:200px;min-width:200px;max-width:200px;">Date</th>'+
                '</tr></thead>';
                comments = comments + '<tbody>';

                var count = 0;
                for (x in data["comments"]) {
                    comments = comments + '<tr>'+
                        '<td>' + data["comments"][x]["user"] + '</td>'+
                        '<td>' + data["comments"][x]["comment"] + '</td>'+
                        '<td>' + data["comments"][x]["date"] + '</td>'+
                    '</tr>';
                    count+=1;
                }

                comments = comments + '</tbody>';
                comments = comments + '</table>';
                $("#commentsTableVar").html(comments);
                $('.commentsCountVar').html(count);

                $('#tableCommentsVar').DataTable({
                    searching:false,
                    lengthMenu: [ 10 ],
                    dom: 'tip',
                    order: [[ 2, "desc" ]],
                    columnDefs: [{
                        orderable: false,
                        targets:  "no-sort"
                    }],
                });
            });
        } else {
            $.getJSON("/json/comments/sample/" + sample_id, function(data) {
                $('.commentsCountSample').html(data.data.length);
            });
            $("#comment_sample").val("");
            $('#tableCommentsSample').DataTable().ajax.reload();
        }
    });
}

function saveFilter() {
    var name = $("#filterName").val();
    var filter = JSON.parse($("#filterText").text());
    var teams = [];
    var elt = $("#create-filter").find('.select2-container').find('.selection').find('.select2-selection').find('.select2-selection__rendered').find('.select2-selection__choice');
    for (i in [...Array(elt.length).keys()]) {
        teams.push(elt[i].title);
    }
    $.ajax({
        type: "POST",
        url: "/add/filter",
        data: {
            name: name,
            filter: JSON.stringify(filter),
            teams: JSON.stringify(teams),
            edit: false
        }
    }).done(function() {
        $('#filter-modal').toggle();
        $.getJSON("/json/filters", function(data) {
            var options = "";
            for (x in data) {
                option = '<option value="' + x + '" '
                if (data[x] == name) {
                    option += "selected"
                }
                if (x == current_user_filter_id) {
                    option += '>' + data[x] + ' (default)</option>';
                } else {
                    option += '>' + data[x] + '</option>';
                }
                options += option;
            }
            $('#selectFilter').html(options);
        });
    }).fail(function (jqXHR, textStatus) {
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: 'Something went wrong!',
            footer: jqXHR["responseText"]
        })
    })
}
function applied_panel(id, sample_id) {
    $('#variants').DataTable()
        .clear()
        .draw();
    $('td.dataTables_empty', $('#variants')).html('<div class="animation-bar-1"><span style="width:100%"></span></div>');

    $.ajax({
        type: "POST",
        url: "/toggle/sample/panel",
        data: {
            "id_sample": sample_id,
            "id_panel": id
        },
        success: function(count_hide) {
            $('#tableHistorySample').DataTable().ajax.reload();
            hide_message(count_hide);
        }
    });
    table = $('#variants').DataTable();
    $('#reload-button').html("<span>Reload table</span>");
    table.ajax.url( '/json/variants/sample/' + sample_id + '/bed/' + id ).load(function(){$("#variants").css('opacity', '1');});
}
$('.js-example-basic-multiple').select2();


$(document).on("click", function(event){
    if($(event.target).parents('.button-class').length || $(event.target).hasClass('button-class')) {
        return;
    }
    $('.ClassVisible').toggle();
    $('.ClassVisible').removeClass("ClassVisible");
});
function toggle_dd_class(id) {
    if (! $('#' + id +'-content').hasClass("ClassVisible")) {
        $('.ClassVisible').hide();
        $('.ClassVisible').removeClass("ClassVisible");
    }
    right = $(window).width() - $('#' + id).offset().left - $('#' + id).outerWidth();
    $('#' + id +'-content').css('margin-right', right);
    $('#' + id +'-content').toggle();
    $('#' + id +'-content').toggleClass("ClassVisible");
}


$('#tableCommentsSample').DataTable({
    searching:false,
    lengthMenu: [ 10 ],
    dom: 'tip',
    order: [[ 2, "desc" ]],
    columnDefs: [
        {
            orderable: false,
            targets:  "no-sort"
        }
    ],
    ajax: "/json/comments/sample/" + sample_id,
    columns:[
        {
            data: "username",
        },
        {
            data: "comment",
        },
        {
            data: "date",
        }
    ]

});
var families=[];
$.getJSON('/json/families', function(data, status, xhr){
    for (var i = 0; i < data['data'].length; i++ ) {
        families.push(data["data"][i]["family"]);
    }
});

$('#edit-family').autocomplete({
    source: families,
});

$("#edit-family").keyup(function(event) {
    if (event.keyCode === 13) {
        edit_family()
    }
});

function edit_family() {
    Swal.fire({
        title: 'Are you sure?',
        text: "You change the family associated to the sample.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, change it!'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire(
                'Changed!',
                'The family will be changed.',
                'success'
            )
            $.ajax({
                type: "POST",
                url: "/edit/sample/family",
                data: {
                    "sample_id": sample_id,
                    "new_family": $('#edit-family').val()
                },
                success: function() {
                    $( "#error-message-edit-family" ).remove();
                    $('#tableHistorySample').DataTable().ajax.reload();
                },
                error: function(XMLHttpRequest) {
                    $( "#error-message-edit-family" ).remove();
                    msg = "<p id='error-message-edit-family' class='w3-small w3-text-flat-alizarin' style='margin:0px'><i class='fas fa-exclamation-circle'></i> " + XMLHttpRequest["responseJSON"]["message"] + "</p>"
                    $( "#sample-family-sidebar" ).after( msg );
                }
            })
        }
    })
}


$(document).ready(function() {
    $('#tableHistorySample').DataTable({
        searching:true,
        processing: true,
        lengthMenu: [ 10 ],
        dom: 'tip',
        order: [[ 2, "desc" ]],
        columnDefs: [
            {
                orderable: false,
                targets:  "no-sort"
            }
        ],
        ajax: '/json/history/sample/' + sample_id,
        columns: [
            {
                data: "user",
            },
            {
                data: "action",
            },
            {
                data: "date",
            }
        ]
    });
});