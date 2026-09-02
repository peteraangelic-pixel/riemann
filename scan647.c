/* Erdős #647: find n>24 with max_{m<n}(m+tau(m)) <= n+2.  Segment sieve, 64-bit. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

int main(int argc, char** argv){
    uint64_t N = argc>1 ? strtoull(argv[1],0,0) : 1000000000ULL;
    uint64_t SEG = 1<<22;
    uint64_t sq = (uint64_t)sqrtl((long double)N)+1;
    unsigned char *iscomp = calloc(sq+1,1);
    int *primes = NULL; size_t np=0, cap=0;
    for(uint64_t i=2;i<=sq;i++) if(!iscomp[i]){
        for(uint64_t j=i*i;j<=sq;j+=i) iscomp[j]=1;
        if(np==cap){cap=cap?cap*2:1024; primes=realloc(primes,cap*sizeof(int));}
        primes[np++]=(int)i;
    }
    int64_t *cur = malloc(SEG*sizeof(int64_t));
    int *tau = malloc(SEG*sizeof(int));
    uint64_t hits=0, prev_tau=0; /* tau of m=a-1 (carried) */
    uint64_t M=0;
    for(uint64_t a=2; a<=N; a+=SEG){
        uint64_t b = a+SEG-1; if(b>N) b=N;
        uint64_t L = b-a+1;
        for(uint64_t i=0;i<L;i++){ cur[i]=a+i; tau[i]=1; }
        for(size_t pi=0; pi<np; pi++){
            int p = primes[pi];
            if((uint64_t)p > b) break;
            uint64_t start = ((a+p-1)/p)*p;
            for(uint64_t m=start; m<=b; m+=p){
                int e=0;
                while(cur[m-a]%p==0){ cur[m-a]/=p; e++; }
                tau[m-a] *= (e+1);
            }
        }
        for(uint64_t m=a;m<=b;m++) if(cur[m-a]>1) tau[m-a]*=2;
        for(uint64_t n=a;n<=b;n++){
            uint64_t m=n-1;
            uint64_t tm;
            if(m>=a) tm=tau[m-a];
            else tm=prev_tau;
            uint64_t v=m+tm;
            if(v>M) M=v;
            if(n>24 && M<=n+2){ printf("HIT n=%llu M=%llu\n",(unsigned long long)n,(unsigned long long)M); hits++; fflush(stdout);}
            if(hits>=100) goto done;
        }
        prev_tau = tau[L-1];
    }
done:
    printf("done N=%llu hits=%llu\n",(unsigned long long)N,(unsigned long long)hits);
    return 0;
}
