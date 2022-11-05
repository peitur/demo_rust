#!/usr/bin/python3

import os, re, sys
import pathlib, json
import tarfile

import subprocess, shlex
from pprint import pprint


DEFAULT_SOURCE="trailer"
DEFAULT_TARGET="vendor"
CARGO_FILE="Cargo.toml"

class GenericCommand( object ):
    
    def __init__( self, cmd, **opt ):
        self.__debug = opt.get("debug", False )
        self.__data = list()        
        self.__cmd  = cmd
        self.__opt = opt
        
        if type( cmd ).__name__ in ( "str" ):
            self.__cmd  = shlex.split( cmd )
        else:
            self.__cmd  = [ str( s ) for s in  cmd ]

    def run_iterator( self ):

        if self.__debug: print( "CMD Running:> '%s'" % ( " ".join( self.__cmd ) ) )
        if self.__just_print:
             return ( 0, list() )
         
        prc = subprocess.Popen( self.__cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, cwd=self.__opt.get( "cwd", None ), universal_newlines=True, shell=False )
        for line in prc.stdout.readlines():
            yield line.rstrip()
            
            if prc.poll():
                break
            
        return ( prc.returncode, list() )
        

    def run_list( self ):

        res = list()
        
        if self.__debug: print( "CMD Running:> '%s'" % ( " ".join( self.__cmd ) ) )

        prc = subprocess.Popen( self.__cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, cwd=self.__opt.get( "cwd", None ), universal_newlines=True, shell=False )
        for line in prc.stdout.readlines():
            res.append( line.rstrip() )
            
            if prc.poll():
                break
            
        return ( prc.returncode, res )



def _read_text( filename ):
    result = list()
    try:
        fd = open( filename, "r" )
        for line in fd.readlines():
            result.append( line.lstrip().rstrip() )
        return result
    except Exception as e:
        print("ERROR Reading %s: %s" % ( filename, e ))

    return result

def _read_json( filename ):
    return json.loads( "\n".join( _read_text( filename ) ) )

def load_file( filename ):
    filesplit = re.split( r"\.", filename )
    if filesplit[-1] in ( "json" ):
        return _read_json( filename )
    else:
        return _read_text( filename )


def _write_json( filename, data ):
    return _write_text( filename, json.dumps( data, indent=2, sort_keys=True ) )

def _write_text( filename, data ):
    fd = open( filename, "w" )
    fd.write( str( data ) )
    fd.close()

def write_file( filename, data ):
    filesplit = re.split( "\.", filename )
    if filesplit[-1] in ( "json" ):
        return _write_json( filename, data )
    else:
        return _write_text( filename, data )


def cargo_meta_file( filepath, filename=CARGO_FILE ):
    values = dict()
    cfile = "%s/%s" % ( dir, filename )
    with open( cfile, "r" ) as fd:
        for line in fd.readlines():
            line = line.rstrip().lstrip()
            if re.match( r"^\s*#.*" , line ) or len( line ) == 0:
                continue
            values.append( line )
    return values
            
            
def cargo_meta_pkg( pkgfile ):

    result = list()

    try:
        tar = tarfile.open( pkgfile, "r:gz")
        p = re.compile( r"[^/]+/%s" % (CARGO_FILE) )
        for ti in tar.getmembers():
            if p.match( ti.name ):
                result = [ x.decode("utf-8").lstrip().rstrip() for x in tar.extractfile( ti.name ).readlines() ]

    except KeyError as e:
        return list()
    finally:
        tar.close()
    return result



def cargo_meta_parse( data ):
    values = dict()
    ctag = ""
    for line in data:
        line = line.rstrip().lstrip()

        if re.match( r"^\s*#.*" , line ) or len( line ) == 0:
            continue

        c_rx = re.match( r"\[\s*(\S+)\s*\]", line )
        if c_rx:
            ctag = c_rx.group(1)
        
        l_rx = re.match( r"^\s*(\S+)\s*=\s*\"(.+)\"", line )
        if l_rx:
            values[ "%s.%s" % ( ctag, l_rx.group(1)) ] = l_rx.group(2)
                
    return values


def rmdir_tree( path ):
    pth = pathlib.Path( path )
    for sub in pth.iterdir() :
        if sub.is_dir() :
            rmdir_tree(sub)
        else:
            sub.unlink()
    pth.rmdir()

def get_crates( dir ):
    return [ f for f in pathlib.Path( dir ).iterdir() if re.match( ".+\.crate$", f.name ) ]

if __name__ == "__main__":
    
    pprint( cargo_meta_parse( cargo_meta_pkg( "trailer/chrono-0.4.22.crate") ) )

    