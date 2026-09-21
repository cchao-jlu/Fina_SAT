/****************************************************************************************[Dimacs.h]
Copyright (c) 2003-2006, Niklas Een, Niklas Sorensson
Copyright (c) 2007-2010, Niklas Sorensson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
**************************************************************************************************/

#ifndef Glucose_Dimacs_h
#define Glucose_Dimacs_h

#include <cerrno>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <stdio.h>
#include <string>
#include <vector>

#include "utils/ParseUtils.h"
#include "core/SolverTypes.h"

namespace Glucose {

//=================================================================================================
// DIMACS Parser:

template<class Solver>
static void newDimacsVar(Solver& S, const std::vector<double>& signed_scales) {
    int var = S.nVars();
    if (var >= static_cast<int>(signed_scales.size())) {
        S.newVar();
        return;
    }

    double signed_scale = signed_scales[var];
    bool phase = signed_scale > 0.0;
    double scale = signed_scale < 0.0 ? -signed_scale : signed_scale;
    if (scale == 0.0) scale = 1.0;
    S.newVar(!phase, true, 0.0, scale);
}

template<class B>
static bool eagerMatchWeight(B& in) {
    if (!eagerMatch(in, "c weight")) return false;
    return *in == EOF || *in == '\n' || *in == '\r' ||
        std::isspace(static_cast<unsigned char>(*in));
}

template<class B, class Solver>
static void readClause(
    B& in,
    Solver& S,
    vec<Lit>& lits,
    const std::vector<double>& signed_scales,
    int declared_vars,
    bool weighted
) {
    int     parsed_lit, var;
    lits.clear();
    for (;;){
        parsed_lit = parseInt(in);
        if (parsed_lit == 0) break;
        var = abs(parsed_lit)-1;
        if (weighted && (var < 0 || var >= declared_vars)) {
            fprintf(stderr, "PARSE ERROR! weighted literal is outside the declared variable range.\n");
            exit(3);
        }
        while (var >= S.nVars()) newDimacsVar(S, signed_scales);
        lits.push( (parsed_lit > 0) ? mkLit(var) : ~mkLit(var) );
    }
}

template<class B>
static void readWeightLine(B& in, int vars, std::vector<double>& signed_scales) {
    std::string line;
    while (!isEof(in) && *in != '\n' && *in != '\r') {
        line.push_back(static_cast<char>(*in));
        ++in;
    }
    if (*in == '\r') {
        ++in;
        if (*in == '\n') ++in;
    } else if (*in == '\n') {
        ++in;
    }

    signed_scales.clear();
    const char* cursor = line.c_str();
    while (*cursor != '\0') {
        while (*cursor != '\0' && std::isspace(static_cast<unsigned char>(*cursor))) cursor++;
        if (*cursor == '\0') break;

        errno = 0;
        char* token_end = NULL;
        double signed_scale = std::strtod(cursor, &token_end);
        if (token_end == cursor || errno == ERANGE || !std::isfinite(signed_scale)) {
            fprintf(stderr, "PARSE ERROR! c weight requires finite numeric values.\n");
            exit(3);
        }
        if (*token_end != '\0' && !std::isspace(static_cast<unsigned char>(*token_end))) {
            fprintf(stderr, "PARSE ERROR! c weight contains an invalid numeric token.\n");
            exit(3);
        }
        signed_scales.push_back(signed_scale);
        cursor = token_end;
    }

    if (signed_scales.size() != static_cast<size_t>(vars)) {
        fprintf(
            stderr,
            "PARSE ERROR! c weight expected exactly %d finite values, found %zu.\n",
            vars,
            signed_scales.size()
        );
        exit(3);
    }

}

template<class B, class Solver>
static void parse_DIMACS_main(B& in, Solver& S) {
    vec<Lit> lits;
    int vars    = 0;
    int clauses = 0;
    int cnt     = 0;
    bool header_seen = false;
    bool has_weight_line = false;
    bool clauses_started = false;
    std::vector<double> signed_scales;
    for (;;){
        skipWhitespace(in);
        if (*in == EOF) break;
        else if (*in == 'p'){
            if (eagerMatch(in, "p cnf")){
                if (header_seen || has_weight_line || clauses_started) {
                    fprintf(stderr, "PARSE ERROR! duplicate or out-of-order problem header.\n");
                    exit(3);
                }
                vars    = parseInt(in);
                clauses = parseInt(in);
                header_seen = true;
            }else{
                printf("PARSE ERROR! Unexpected char: %c\n", *in), exit(3);
            }
        } else if (*in == 'c')
            if (eagerMatchWeight(in)){
                if (!header_seen || has_weight_line || clauses_started) {
                    fprintf(stderr, "PARSE ERROR! c weight is out of order or duplicated.\n");
                    exit(3);
                }
                readWeightLine(in, vars, signed_scales);
                has_weight_line = true;
            }else{
                skipLine(in);
            }
        else{
            if (!header_seen) {
                fprintf(stderr, "PARSE ERROR! clause encountered before problem header.\n");
                exit(3);
            }
            cnt++;
            clauses_started = true;
            readClause(in, S, lits, signed_scales, vars, has_weight_line);
            S.addClause_(lits); }
    }
    if (has_weight_line)
        while (S.nVars() < vars) newDimacsVar(S, signed_scales);
    if (vars != S.nVars())
        fprintf(stderr, "WARNING! DIMACS header mismatch: wrong number of variables.\n");
    if (cnt  != clauses)
        fprintf(stderr, "WARNING! DIMACS header mismatch: wrong number of clauses.\n");
}

// Inserts problem into solver.
//
template<class Solver>
static void parse_DIMACS(gzFile input_stream, Solver& S) {
    StreamBuffer in(input_stream);
    parse_DIMACS_main(in, S); }

//=================================================================================================
}

#endif
