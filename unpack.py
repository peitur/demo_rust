#!/usr/bin/python3

import os, re, sys
import pathlib, json
import tarfile
import logging

import subprocess, shlex
from pprint import pprint


DEFAULT_SOURCE="trailer"
DEFAULT_TARGET="vendor"
CARGO_FILE="Cargo.toml"

CRAATE_IMPORT_OVERWRITE=True



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
    values = list()
    cfile = "%s/%s" % ( filepath, filename )
    with open( cfile, "r" ) as fd:
        for line in fd.readlines():
            line = line.rstrip().lstrip()
            if re.match( r"^\s*#.*" , line ) or len( line ) == 0:
                continue
            values.append( line )
    return values
            
            
def cargo_meta_pkg( pkgfile ):
    try:
        tar = tarfile.open( pkgfile, "r:gz")
        p = re.compile( r"[^/]+/%s" % (CARGO_FILE) )
        for ti in tar.getmembers():
            if p.match( ti.name ):
                return [ x.decode("utf-8").lstrip().rstrip() for x in tar.extractfile( ti.name ).readlines() ]

    except KeyError as e:
        raise IndexError("Invalid crate file")
    finally:
        tar.close()
    raise IndexError("Invalid crate file, no metadata file found")

def cargo_meta_unpack_path( pkgfile ):
    try:
        tar = tarfile.open( pkgfile, "r:gz")
        p = re.compile( r"[^/]+/%s" % (CARGO_FILE) )
        for ti in tar.getmembers():
            if p.match( ti.name ):
                return pathlib.Path( ti.name ).parent

    except KeyError as e:
        raise IndexError("Invalid crate file")
    finally:
        tar.close()
    raise IndexError("Invalid crate file, no metadata file found")


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


def cargo_extract_source( cratefile,  tpath="." ):
    if not cargo_check_source( cratefile ):
        RuntimeError("Dangerous archive file \"%s\", skipping" % ( cratefile ) )
    try:
        tar = tarfile.open( cratefile )
        tar.extractall( tpath )
    except:
        return False
    finally:
        tar.close()
    return True

def cargo_check_source( pkgfile ):
     
    rxl = [ re.compile("^/.+"), re.compile("\.\./") ]
     
    try:
        tar = tarfile.open( pkgfile, "r:gz")
        for ti in tar.getmembers():
            
            for rx in rxl:
                if rx.match( ti.name ):
                    return False

    except KeyError as e:
        raise IndexError("Invalid crate file")
    finally:
        tar.close()
    return True

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
    
    known_cratews = dict()
    try:
        spath = sys.argv[1]
        tpath = sys.argv[2]
        
        crate_list = get_crates( spath )
        
        print( "Reading crates from \"%s\"" % ( spath ) )
        print( "Importing to \"%s\"" % ( tpath ) )
        print("Found %s crates in \"%s\"" % ( len( crate_list), spath) )
        for crate in crate_list:
            filename =  crate.name
            crt_meta = cargo_meta_parse( cargo_meta_pkg( str( crate ) ) )
            
            print(" - \"%s\" = \"%s\" # \"%s\"" % ( crt_meta['package.name'], crt_meta['package.version'], filename ), end=" " )

            if cargo_extract_source( str( crate ), tpath ):
                crt_unp_name = cargo_meta_unpack_path( str( crate ) )
                crt_unp_path = pathlib.Path( "%s/%s" % ( tpath, crt_unp_name ) )
                crt_target = pathlib.Path( "%s/%s" %( tpath, crt_meta['package.name'] ) )
                crt_rollback_path = pathlib.Path("%s.old" % ( crt_target ) )
                
                if not crt_unp_path.exists():
                    raise OSError("Could not intended crate directory \"%s\"" % ( crt_unp_path ) )
                
                if crt_target.exists() and CRAATE_IMPORT_OVERWRITE:
                    inst_crt_meta = cargo_meta_parse( cargo_meta_file( str( crt_target ) ) )
                    print( ": Found crate \"%s\" version \"%s\", overwriting with version \"%s\"" % ( inst_crt_meta['package.name'], inst_crt_meta['package.version'], crt_meta['package.version'] ), end=" " )
                    crt_target.rename( crt_rollback_path )
                
                try:
                    crt_unp_path.rename( crt_target )
                    if crt_rollback_path.exists( ) and CRAATE_IMPORT_OVERWRITE:
                        rmdir_tree( str( crt_rollback_path ) )
                except:
                    if crt_rollback_path.exists():
                        crt_rollback_path.rename( crt_target )
            print()
            
    except Exception as e:
        raise 



    